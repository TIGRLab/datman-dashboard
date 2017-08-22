"""
Config file for dashboard webapp
In production environment variables are defined in:
    /etc/uwsgi/apps-available/dashboard.ini
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED = True
SECRET_KEY = 'bet-you-cant-guess'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'dashboard.sqlite')
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pwd}@{srvr}/{db}'.format(user=os.environ.get('POSTGRES_USER'),
                                                                               pwd=os.environ.get('POSTGRES_PASS'),
                                                                               srvr=os.environ.get('POSTGRES_SRVR'),
                                                                               db=os.environ.get('POSTGRES_DATABASE'))
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True #This should be turned off after development

# mail server settings
MAIL_SERVER = "smtp.camh.net"
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None

LOGSERVER = '172.26.216.101'
# administrator list
ADMINS = ['tom@maladmin.com',
          'dawn.smith@camh.ca',
          'admins@tigrsrv.camhres.ca']


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

DISPLAY_METRICS = {'phantom': {'t1': ['c1', 'c2', 'c3', 'c4'],
                              'dti': ['AVENyqratio', 'AVE Ave.radpixshift', 'AVE Ave.colpixshift', 'aveSNR_dwi'],
                              'fmri': ['sfnr', 'rdc']},
                   'human': {'t1': [],
                            'dti': ['tsnr_bX', 'meanRELrms', '#ndirs', 'Spikecount'],
                            'fmri': ['mean_fd', 'mean_sfnr', 'ScanLength']}}

REDCAP_TOKEN = os.environ.get('REDCAP_TOKEN')
