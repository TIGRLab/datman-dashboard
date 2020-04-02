"""Email functions used by the redcap blueprint.
"""

from dashboard.emails import send_email


def missing_session_data(session, study=None, dest_emails=None):
    subject = "No data received for '{}'".format(session)
    if study:
        subject = study + "- " + subject
    body = "It has been 48hrs since a redcap scan completed survey was " \
           "received for {} but no scan data has been found.".format(session)
    send_email(subject, body, recipient=dest_emails)
