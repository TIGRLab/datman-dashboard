import logging
from threading import Thread

from flask import url_for
from flask_mail import Message

from dashboard import app, mail, SENDER, ADMINS, DASH_SUPPORT

logger = logging.getLogger(__name__)


def async_exec(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


@async_exec
def send_async_email(app, email):
    with app.app_context():
        mail.send(email)


def send_email(subject, body, html_body=None, recipient=None):
    if not recipient:
        recipient = ADMINS
    if not isinstance(recipient, list):
        recipient = [recipient]
    email = Message(subject, sender=SENDER, recipients=recipient)
    email.body = body
    if html_body:
        email.html = html_body
    send_async_email(app, email)


def incidental_finding_email(user, timepoint, comment):
    subject = "IMPORTANT: Incidental Finding flagged"
    body = "{} has reported an incidental finding for {}. Description: {}".format(
        user, timepoint, comment
    )
    send_email(subject, body)


def account_request_email(first_name, last_name):
    subject = "New account request from {} {}".format(first_name, last_name)
    body = (
        "{} {} has requested a dashboard account. Please log in to "
        "approve or reject this request".format(first_name, last_name)
    )
    try:
        dest_url = url_for("manage_users", _external=True)
    except:
        html_body = body
    else:
        html_body = (
            "{} {} has requested dashboard access. <a href='{}'>"
            "Click here</a> to review and approve/reject the request".format(
                first_name, last_name, dest_url
            )
        )
    send_email(subject, body, html_body=html_body)


def account_activation_email(user):
    if not user.email:
        logger.error(
            "Can't send account activation email to user {}. No "
            "email address available.".format(user.id)
        )
        return
    subject = "QC Dashboard account activated"
    body = (
        "You can now log in to the QC dashboard using account {}. You "
        "can currently access {} studies. Access to additional studies "
        "can be requested by filling in the study request form found on "
        "your profile page after logging in.".format(user.username,
                                                     len(user.studies))
    )
    send_email(subject, body, recipient=user.email)


def account_rejection_email(user):
    if not user.email:
        logger.error(
            "Can't send account request rejection email to user {}."
            "No email address available".format(user.id)
        )
        return
    subject = "QC Dashboard account request rejected"
    body = (
        "An admin has reviewed your request for access to the QC dashboard "
        "and unfortunately it has been rejected. For any questions you "
        "may have please contact us at {}".format(DASH_SUPPORT)
    )
    send_email(subject, body, recipient=user.email)


def missing_redcap_email(session, study=None, dest_emails=None):
    subject = "Missing REDCap Survey"
    if study:
        subject = study + "- " + subject
    body = (
        "A 'Scan Completed' survey is expected for session '{}' but a "
        "survey has not been received. Please remember to fill out the "
        "survey or let us know if this email is in error.".format(session)
    )
    send_email(subject, body, recipient=dest_emails)


def missing_session_data_email(session, study=None, dest_emails=None):
    subject = "No data received for '{}'".format(session)
    if study:
        subject = study + "- " + subject
    body = (
        "It has been 48hrs since a redcap scan completed survey was "
        "received for {} but no scan data has been found.".format(session)
    )
    send_email(subject, body, recipient=dest_emails)


def unsent_notification_email(user, type, unsent_body):
    subject = "Unable to send '{}' notification to user {}".format(type, user)
    body = "Failed to send email to user {} with body: \n\n {}".format(
        user.id, unsent_body
    )
    send_email(subject, body)


def qc_needed_email(session, study, dest_emails):
    subject = "[{}] - New Scan, QC Needed".format(study)
    body = (
            "New scan acquired for {}\nSession: {}\n"
            "Please QC as soon as possible".format(study, session)
    )
    send_email(subject, body, recipient=dest_emails)
