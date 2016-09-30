import os

basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED = True
SECRET_KEY = 'bet-you-cant-guess'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'dashboard.sqlite')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True #This should be turned off after development
