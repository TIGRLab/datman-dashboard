"""
Config file for dashboard webapp
In production environment variables are defined in:
    /etc/uwsgi/apps-available/dashboard.ini
"""
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler.auth import HTTPBasicAuth

def read_boolean(var_name, default=False):
    try:
        result = os.environ.get(var_name).lower()
    except AttributeError:
        result = ""
    if result == "":
        return default
    if result == 'true' or result == 'on':
        return True
    return False

## Flask settings ##############################################################
WTF_CSRF_ENABLED = True
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

################################################################################
## SQLAlchemy settings #########################################################
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pwd}@{srvr}/{db}'.format(
        user=os.environ.get('POSTGRES_USER'),
        pwd=os.environ.get('POSTGRES_PASS'),
        srvr=os.environ.get('POSTGRES_SRVR'),
        db=os.environ.get('POSTGRES_DATABASE'))

# Timezone offset used for timezone aware timestamps. Default is Eastern time
# See https://docs.python.org/2/library/datetime.html#datetime.datetime.now
TZ_OFFSET = os.environ.get('TIMEZONE') or -240

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'migrations')
SQLALCHEMY_TRACK_MODIFICATIONS = False

################################################################################
## OAuth settings ##############################################################
OPENID_PROVIDERS = [
    {'name': 'GitHub',
     'url': "https://github.com/login/oauth/authorize"}
]

OAUTH_CREDENTIALS = {'github': {'id': os.environ.get('OAUTH_CLIENT_GITHUB'),
                                'secret': os.environ.get('OAUTH_SECRET_GITHUB')
                                },
                     'gitlab': {'id': os.environ.get('OAUTH_CLIENT_GITLAB'),
                                'secret': os.environ.get('OAUTH_SECRET_GITLAB')
                                }}

################################################################################
## Issues settings #############################################################
GITHUB_OWNER = os.environ.get('GITHUB_ISSUES_OWNER')
GITHUB_REPO = os.environ.get('GITHUB_ISSUES_REPO')
GITHUB_PUBLIC = read_boolean("GITHUB_ISSUES_PUBLIC", default=True)

################################################################################
## Mail settings ###############################################################
# These dont need to be imported anywhere, they're read when
# app.config.from_object('config') is run in init and read by the flask_mail
# extension when Mail(app) is run
MAIL_SERVER = os.environ.get("DASHBOARD_MAIL_SERVER") or "smtp.gmail.com"
MAIL_PORT = os.environ.get("DASHBOARD_MAIL_PORT") or 465
MAIL_USERNAME = os.environ.get("DASHBOARD_MAIL_UNAME") or None
MAIL_PASSWORD = os.environ.get("DASHBOARD_MAIL_PASS") or None
DASH_SUPPORT = os.environ.get("DASHBOARD_SUPPORT_EMAIL") or MAIL_USERNAME
SENDER = DASH_SUPPORT or MAIL_USERNAME or "no-reply@kimellab.ca"
MAIL_USE_SSL = read_boolean("DASHBOARD_MAIL_SSL", default=True)

################################################################################
## Logging settings ############################################################
LOGSERVER = os.environ.get("DASHBOARD_LOG_SERVER")

LOG_MAIL_SERVER = os.environ.get("DASH_LOG_EMAIL") or 'smtp.camh.net'
LOG_MAIL_PORT = os.environ.get("DASH_LOG_PORT") or 25
LOG_MAIL_USER = None
LOG_MAIL_PASS = None

################################################################################
## Scheduler settings ##########################################################
SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
}

SCHEDULER_JOB_DEFAULTS = {
        'coalesce': True,
        'misfire_grace_time': 3600
}

# This starts an instance of the scheduler (for sending scheduled notifications,
# etc.). You only want this to be true on the server, not instances where the
# dashboard has been imported
SCHEDULER_ENABLED = read_boolean("DASHBOARD_SCHEDULER")

# This turns on the API. You only want this to be true on the server,
# not on imported instances, and only if you want to allow people to submit
# jobs over the network (i.e. to add jobs from scripts that import the
# dashboard)
SCHEDULER_API_ENABLED = read_boolean("DASHBOARD_SCHEDULER_API")

if SCHEDULER_API_ENABLED:
    # This is needed to password protect the API (HTTP basic auth is the
    # strongest the flask-apscheduler allows, but should not be used over the
    # open internet)
    SCHEDULER_AUTH = HTTPBasicAuth()

# Needs to be set for server and any client instances that will use the
# scheduler API
SCHEDULER_USER = os.environ.get('DASHBOARD_SCHEDULER_USER')
SCHEDULER_PASS = os.environ.get('DASHBOARD_SCHEDULER_PASS')

# This is only needed on imported instances of the dashboard so they know
# which url to send jobs to
SCHEDULER_SERVER_URL = os.environ.get("DASHBOARD_URL")

################################################################################
## Other settings ##############################################################

# administrator email list
try:
    ADMINS = os.environ.get("ADMINS").split(",")
except AttributeError:
    ADMINS = ""

# For retrieving records after a data entry trigger is received
REDCAP_TOKEN = os.environ.get('REDCAP_TOKEN')

# This probably needs to be scrapped / changed when we fix our metrics +
# graphs and stuff
DISPLAY_METRICS = {'phantom': {'t1': ['c1', 'c2', 'c3', 'c4'],
                              'dti': ['AVENyqratio', 'AVE Ave.radpixshift',
                                      'AVE Ave.colpixshift', 'aveSNR_dwi'],
                              'fmri': ['sfnr', 'rdc']},
                   'human': {'t1': [],
                            'dti': ['tsnr_bX', 'meanRELrms', '#ndirs',
                                    'Spikecount'],
                            'fmri': ['mean_fd', 'mean_sfnr', 'ScanLength']}}

################################################################################
