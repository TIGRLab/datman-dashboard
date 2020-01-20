"""Any email related configuration

Used by Flask-Mail extension, emailed logs, etc.
"""
import os

from .utils import read_boolean

# A comma separated list of dashboard admin emails
try:
    ADMINS = os.environ.get("ADMINS").split(",")
except AttributeError:
    ADMINS = ""


# Server to send all outgoing Flask_Mail emails to.
# Set to 'disabled' to turn off email
MAIL_SERVER = os.environ.get("DASHBOARD_MAIL_SERVER") or "smtp.gmail.com"

if MAIL_SERVER.lower() == 'disabled':
    # Turn off emails. If app is in testing mode emails will be
    # automatically turned off regardless of value of 'MAIL_SERVER'
    MAIL_SUPPRESS_SEND = True

# Port on MAIL_SERVER that the email server listens to
MAIL_PORT = os.environ.get("DASHBOARD_MAIL_PORT") or 465

# Username to authenticate with on MAIL_SERVER. Set to None if
# authentication not required
MAIL_USERNAME = os.environ.get("DASHBOARD_MAIL_UNAME") or None

# Password to authenticate with on MAIL_SERVER. Set to None if
# authentication not required
MAIL_PASSWORD = os.environ.get("DASHBOARD_MAIL_PASS") or None

# Email address to direct support requests to.
DASH_SUPPORT = os.environ.get("DASHBOARD_SUPPORT_EMAIL") or MAIL_USERNAME

# Email to set as the 'sender' on all outgoing emails
SENDER = DASH_SUPPORT or MAIL_USERNAME or "no-reply@kimellab.ca"

# Whether to use SSL when sending email. This depends on how the 'MAIL_SERVER'
# is configured. For gmail it must be true for email to be forwarded.
MAIL_USE_SSL = read_boolean("DASHBOARD_MAIL_SSL", default=True)


# Server to send outgoing log emails to. Set to 'disabled' to turn off
# emailed logs completely.
LOG_MAIL_SERVER = os.environ.get("DASH_LOG_MAIL_SERVER") or 'smtp.camh.net'

if LOG_MAIL_SERVER.lower() == 'disabled':
    # Turn off log emails. They will NOT be automatically disabled when
    # the app is run in testing mode.
    LOG_MAIL_SERVER = None

# Port on LOG_MAIL_SERVER to use when forwarding emails
LOG_MAIL_PORT = os.environ.get("DASH_LOG_MAIL_PORT") or 25

# Username to authenticate on LOG_MAIL_SERVER. Set to None if authentication
# not required.
LOG_MAIL_USER = os.environ.get("DASH_LOG_MAIL_USER") or None

# Password to authenticate with on LOG_MAIL_SERVER. Set to None if
# authentication not required.
LOG_MAIL_PASS = os.environ.get("DASH_LOG_MAIL_PASS") or None
