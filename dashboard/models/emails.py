"""Email notifications sent from models.py

Email functions used by models are likely to be submitted to the scheduler, and
so special care should be taken to ensure their input arguments are always JSON
serializable types (see here for info on serializable types:
https://docs.python.org/3/library/json.html#json.JSONEncoder).
"""

import logging

from flask import url_for, current_app

from dashboard.emails import send_email

logger = logging.getLogger(__name__)


def account_request_email(name):
    """Notify admins that a new user is requesting dashboard access.

    Args:
        name (:obj:`str`): The real name of the user requesting an account
    """
    subject = "New account request from {}".format(name)
    body = "{} has requested a dashboard account. Please log in to review "\
           "this request".format(name)
    try:
        dest_url = url_for('users.manage_users', _external=True)
    except Exception:
        html_body = body
    else:
        html_body = "{} has requested dashboard access. <a href='{}'>" \
                    "Click here</a> to review and approve/reject the " \
                    "request".format(name, dest_url)
    send_email(subject, body, html_body=html_body)


def account_activation_email(oauth_uname, user_email, num_studies):
    """Notify a user that their dashboard access has been approved.

    Args:
        oauth_uname (:obj:`str`): The OAuth provider account name that the
            new user will access the dashboard through.
        user_email (:obj:`str`): The email account associated with the user.
        num_studies (int): The number of studies this user has been granted
            access to.
    """
    if not user_email:
        logger.error("Can't send account activation email to user {}. No "
                     "email address available.".format(oauth_uname))
        return
    subject = "QC Dashboard account activated"
    body = "You can now log in to the QC dashboard using account {}. You " \
           "can currently access {} studies. Access to additional studies " \
           "can be requested by filling in the study request form found " \
           "on your profile page after logging in.".format(oauth_uname,
                                                           num_studies)
    send_email(subject, body, recipient=user_email)


def account_rejection_email(user_id, user_email):
    """Notify a potential user that they will not be granted dashboard access.

    Args:
        user_id (int): The id for the database record storing the user's info.
        user_email (:obj:`str`): The email address to notify.
    """
    if not user_email:
        logger.error("Can't send account request rejection email to user {}."
                     "No email address available".format(user_id))
        return
    subject = "QC Dashboard account request rejected"
    body = "An admin has reviewed your request for access to the QC " \
           "dashboard and unfortunately it has been rejected. For any " \
           "questions you may have please contact us " \
           "at {}".format(current_app.config['DASH_SUPPORT'])
    send_email(subject, body, recipient=user_email)


def qc_notification_email(user, study, current_tp, remain_tp=None):
    """Notify QCers that there is a new session to review.

    Args:
        user (:obj:`str`): A user's real name.
        study (:obj:`str`): The name of the study that has received data.
        current_tp (:obj:`str`): The name of the timepoint that needs review.
        remain_tp (:obj:`list` of :obj:`str`): A list of names of timepoints
            from this study that are still awaiting quality control.
    """
    subject = "{} - New scan, QC needed".format(study)
    body = "Hi {}, you have been tagged as a QCer for {}".format(user, study)
    body += "\n\nNew scan: {}".format(current_tp)

    if remain_tp:
        body += "\n\nScans still needing QC:\n"
        body += "\n".join(remain_tp)

    body += "\n\nIf you wrongly recieved this email, " \
            "please contact staff at the Kimel Lab"

    send_email(subject, body, recipient=user.email)
