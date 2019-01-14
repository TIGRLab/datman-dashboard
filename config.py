"""
Config file for dashboard webapp
In production environment variables are defined in:
    /etc/uwsgi/apps-available/dashboard.ini
"""

import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = os.path.abspath(os.path.dirname(__file__))

# Timezone offset used for timezone aware timestamps. Default is Eastern time
# See https://docs.python.org/2/library/datetime.html#datetime.datetime.now
TZ_OFFSET = os.environ.get('TIMEZONE') or -240
WTF_CSRF_ENABLED = True
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'dashboard.sqlite')
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pwd}@{srvr}/{db}'.format(user=os.environ.get('POSTGRES_USER'),
                                                                               pwd=os.environ.get('POSTGRES_PASS'),
                                                                               srvr=os.environ.get('POSTGRES_SRVR'),
                                                                               db=os.environ.get('POSTGRES_DATABASE'))
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'migrations')
SQLALCHEMY_TRACK_MODIFICATIONS = True #This should be turned off after development

# mail server settings
MAIL_SERVER = os.environ.get("DASHBOARD_MAIL_SERVER") or "smtp.gmail.com"
MAIL_PORT = os.environ.get("DASHBOARD_MAIL_PORT") or 465
MAIL_USERNAME = os.environ.get("DASHBOARD_MAIL_UNAME") or None
MAIL_PASSWORD = os.environ.get("DASHBOARD_MAIL_PASS") or None
DASH_SUPPORT = os.environ.get("DASHBOARD_SUPPORT_EMAIL") or MAIL_USERNAME
SENDER = DASH_SUPPORT or MAIL_USERNAME or "no-reply@kimellab.ca"
MAIL_USE_SSL = True

# Scheduler settings
SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
}
SCHEDULER_API_ENABLED = False

# administrator list
try:
    ADMINS = os.environ.get("ADMINS").split(",")
except AttributeError:
    ADMINS = ""

LOGSERVER = '172.26.216.101'

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

# Github config, needed for issues
GITHUB_OWNER = os.environ.get('GITHUB_ISSUES_OWNER')
GITHUB_REPO = os.environ.get('GITHUB_ISSUES_REPO')
GITHUB_PUBLIC = os.environ.get('GITHUB_ISSUES_PUBLIC') or True

DISPLAY_METRICS = {'phantom': {'t1': ['c1', 'c2', 'c3', 'c4'],
                              'dti': ['AVENyqratio', 'AVE Ave.radpixshift', 'AVE Ave.colpixshift', 'aveSNR_dwi'],
                              'fmri': ['sfnr', 'rdc']},
                   'human': {'t1': [],
                            'dti': ['tsnr_bX', 'meanRELrms', '#ndirs', 'Spikecount'],
                            'fmri': ['mean_fd', 'mean_sfnr', 'ScanLength']}}

REDCAP_TOKEN = os.environ.get('REDCAP_TOKEN')
