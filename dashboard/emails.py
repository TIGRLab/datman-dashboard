"""Functions for sending email notifications.

If an email message _must_ come from the server side, and isn't sent from
within a view function, then it needs to be submitted to the scheduler. That
means it needs a monitor/check function and should be called by the monitor and
not directly.

Any email notifications that might be submitted to the scheduler must only
receive arguments that are JSON serializable (see here for info on serializable
types: https://docs.python.org/3/library/json.html#json.JSONEncoder).
"""

import logging
from threading import Thread

from flask import current_app
from flask_mail import Message

from dashboard import mail

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
    subject = "Missing REDCap Survey"
    if study:
        subject = study + "- " + subject
    body = "A 'Scan Completed' survey is expected for session '{}' but a " \
           "survey has not been received. Please remember to fill out the " \
           "survey or let us know if this email is in error.".format(session)
    send_email(subject, body, recipient=dest_emails)
