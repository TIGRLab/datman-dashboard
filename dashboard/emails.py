"""Functions for sending email notifications.

If an email message **must** be sent from the server side, and it isn't used
exclusively by view functions (which only run on the server), then it needs to
be given to the scheduler. That means it needs a monitor and a check function.
To learn more about monitor/check functions see :py:mod:`dashboard.monitors`

Any email notifications that might be submitted to the scheduler must only
receive arguments that are JSON serializable.
(`see here <https://docs.python.org/3/library/json.html#json.JSONEncoder>`_
for info on serializable types).
"""

import logging
from threading import Thread
from functools import wraps

from flask import current_app
from flask_mail import Message

from dashboard import mail

logger = logging.getLogger(__name__)


def async_exec(f):
    """Allow a given function to execute in the background.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


@async_exec
def send_async_email(app, email):
    """Send an email in the background.

    Args:
        app (:obj:`flask.Flask`): The current application instance.
        email (:obj:`flask_mail.Message`): The message to send.
    """
    with app.app_context():
        mail.send(email)


def send_email(subject, body, html_body=None, recipient=None):
    """Organize email contents into a message and send it in the background.

    Args:
        subject (str): The subject line.
        body (str): The plain text body of the email.
        html_body (str, optional): An optional HTML formatted version of the
            plain text body. Some email clients are plain text only. If the
            recipient's client can't render HTML they will only receive the
            plain text version.
        recipient (str or :obj:`list` of str, optional): An email address (or
            list of email address) to send the message to. If none is provided
            the message will be sent to the address(es) configured as the
            dashboard admin(s).
    """
    if not recipient:
        recipient = current_app.config['ADMINS']
    if not isinstance(recipient, list):
        recipient = [recipient]
    email = Message(subject,
                    sender=current_app.config['SENDER'],
                    recipients=recipient)
    email.body = body
    if html_body:
        email.html = html_body
    send_async_email(current_app._get_current_object(), email)


def missing_redcap_email(session, study=None, dest_emails=None):
    """Notify that a session that requires a REDCap survey did not receive one.

    Args:
        session (str): A session ID.
        study (str, optional): The study that the session belongs to.
        dest_emails (str or :obj:`list` of str, optional): Email address(es) to
            relay the notification to.
    """
    subject = "Missing REDCap Survey"
    if study:
        subject = study + "- " + subject
    body = "A 'Scan Completed' survey is expected for session '{}' but a " \
           "survey has not been received. Please remember to fill out the " \
           "survey or let us know if this email is in error.".format(session)
    send_email(subject, body, recipient=dest_emails)
