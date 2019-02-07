import os

from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from werkzeug.routing import BaseConverter

from config import basedir, ADMINS, LOG_MAIL_SERVER, LOG_MAIL_PORT, \
        LOG_MAIL_USER, LOG_MAIL_PASS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, \
        MAIL_PASSWORD, SENDER, DASH_SUPPORT, LOGSERVER, GITHUB_OWNER, \
        GITHUB_REPO, GITHUB_PUBLIC, TZ_OFFSET, SCHEDULER_ENABLED, \
        SCHEDULER_API_ENABLED, SCHEDULER_SERVER_URL, SCHEDULER_USER, \
        SCHEDULER_PASS

"""
Main init script, creates the app object and sets up logging
"""

app = Flask(__name__)
app.config.from_object('config')

#from app.database import db_session
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'
lm.refresh_view = 'refresh_login'
mail = Mail(app)
if SCHEDULER_ENABLED:
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    if SCHEDULER_API_ENABLED:
        @scheduler.authenticate
        def authenticate(auth):
            return auth['username'] == SCHEDULER_USER and auth['password'] == SCHEDULER_PASS
else:
    from .task_scheduler import RemoteScheduler
    scheduler = RemoteScheduler(SCHEDULER_USER, SCHEDULER_PASS,
            SCHEDULER_SERVER_URL)


################################################################################
# These settings should only be uncommented for development instances of the
# dashboard
#
# from flask_debugtoolbar import DebugToolbarExtension
# app.debug = True
# toolbar = DebugToolbarExtension(app)
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
################################################################################

# This adds a 'regex' type for app routes.
# See: https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler, RotatingFileHandler, SocketHandler, DEFAULT_TCP_LOGGING_PORT
    credentials = None
    if LOG_MAIL_USER or LOG_MAIL_PASS:
        credentials = (LOG_MAIL_USER, LOG_MAIL_PASS)
    mail_handler = SMTPHandler((LOG_MAIL_SERVER, LOG_MAIL_PORT),
                                SENDER,
                                ADMINS,
                                'Dashboard failure',
                                credentials)
    # base_dir = os.path.dirname(os.path.realpath(__file__))
    # base_dir = os.path.realpath(os.path.join(base_dir, '..'))
    #
    # file_handler = RotatingFileHandler(os.path.join(base_dir,
    #                                                 'logs/dashboard.log'),
    #                                    'a',
    #                                    1 * 1024 * 1024,
    #                                    10)
    # file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

    logserver_handler = SocketHandler(LOGSERVER, DEFAULT_TCP_LOGGING_PORT)

    app.logger.setLevel(logging.DEBUG)
    # file_handler.setLevel(logging.DEBUG)
    logserver_handler.setLevel(logging.DEBUG)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    # app.logger.addHandler(file_handler)
    app.logger.addHandler(logserver_handler)
else:
    app.config['SQLALCHEMY_ECHO'] = True

# Need to import views here to get Flask to build url map based on our routes
# Has to be at the bottom after 'app' is defined.
from dashboard import views, models
