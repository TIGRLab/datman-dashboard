import os

basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED = True
SECRET_KEY = 'bet-you-cant-guess'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'dashboard.sqlite')
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{pwd}@{srvr}/dashboard'.format(user=os.environ.get('POSTGRES_USER'),
                                                                               pwd=os.environ.get('POSTGRES_PASS'),
                                                                               srvr=os.environ.get('POSTGRES_SRVR'))
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True #This should be turned off after development

# mail server settings
MAIL_SERVER = "smtp.camh.net"
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None

# administrator list
ADMINS = ['tom@maladmin.com']


OPENID_PROVIDERS = [
    {'name': 'GitHub',
     'url': "https://github.com/login/oauth/authorize"}
]

OAUTH_CREDENTIALS = {'github': {'id': os.environ.get('OAUTH_CLIENT_GITHUB'),
                                'secret': os.environ.get('OAUTH_SECRET_GITHUB')
                                }}
