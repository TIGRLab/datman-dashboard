"""
Main init script, creates the app object and sets up logging
"""
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler, SocketHandler, \
        DEFAULT_TCP_LOGGING_PORT

from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from werkzeug.routing import BaseConverter

from config import basedir, ADMINS, LOG_MAIL_SERVER, LOG_MAIL_PORT, \
        LOG_MAIL_USER, LOG_MAIL_PASS, MAIL_SERVER, MAIL_PORT, SENDER, \
        DASH_SUPPORT, LOGSERVER, GITHUB_OWNER, GITHUB_REPO, GITHUB_PUBLIC, \
        TZ_OFFSET, SCHEDULER_ENABLED, SCHEDULER_API_ENABLED, \
        SCHEDULER_SERVER_URL, SCHEDULER_USER, SCHEDULER_PASS

app = Flask(__name__)
app.config.from_object('config')

# Set up logging ##############################################################
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s '
                              '- %(message)s')

# This logger handles messages for all the dashboard code
dash_logger = logging.getLogger('dashboard')
dash_logger.setLevel(logging.DEBUG)

# app.logger handles messages from Flask. This includes messages about
# exceptions raised by the dashboard but wont grab logging messages from it
# (hence the 'extra' logger above)
app.logger.setLevel(logging.DEBUG)

if LOGSERVER:
    # Set up logging to a remote log server
    logserver_handler = SocketHandler(LOGSERVER, DEFAULT_TCP_LOGGING_PORT)
    logserver_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(logserver_handler)
    dash_logger.addHandler(logserver_handler)

# In your environment set:
#      FLASK_ENV=development    (for all development mode features,
#                               including debug mode. DON'T USE ON A
#                               PRODUCTION SERVER! Flask >= 1.0 only)
#      FLASK_DEBUG=1            (For extra logging only)
if app.debug:
    # This makes debug mode very, very noisy but can be helpful to uncomment
    # if you're having database query issues
    # app.config['SQLALCHEMY_ECHO'] = True

    if app.env == 'development':
        # This stuff should never run on a production server!
        try:
            from flask_debugtoolbar import DebugToolbarExtension
        except ImportError:
            app.logger.warning("flask-debugtoolbar not installed. "
                               "Install it for extra development server "
                               "goodness :)")
        else:
            toolbar = DebugToolbarExtension(app)
            app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

        # Set up logging to a local file.
        # Logging to a file is too slow for production, but can be helpful for
        # development
        base_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.realpath(os.path.join(base_dir, '..'))
        log_dir = os.path.join(base_dir, 'logs')
        if not os.path.exists(log_dir):
            app.logger.warning(
                "{} does not exist. Make it to receive log "
                "files while in development mode :)".format(log_dir))
        else:
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'dashboard.log'), 'a', 1 * 1024 * 1024,
                10)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            dash_logger.addHandler(file_handler)
else:
    # Set up emails on exceptions/logging.error messages. Probably only want
    # these when not in debug mode.
    credentials = None
    if LOG_MAIL_USER or LOG_MAIL_PASS:
        credentials = (LOG_MAIL_USER, LOG_MAIL_PASS)
    mail_handler = SMTPHandler((LOG_MAIL_SERVER, LOG_MAIL_PORT), SENDER,
                               ADMINS, 'Dashboard failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(formatter)
    app.logger.addHandler(mail_handler)
    dash_logger.addHandler(mail_handler)

###############################################################################

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
            return (auth['username'] == SCHEDULER_USER
                    and auth['password'] == SCHEDULER_PASS)
else:
    from .task_scheduler import RemoteScheduler
    scheduler = RemoteScheduler(SCHEDULER_USER, SCHEDULER_PASS,
                                SCHEDULER_SERVER_URL)


class RegexConverter(BaseConverter):
    # This adds a 'regex' type for app routes.
    # See: https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing  # noqa: E501
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter

# Need to import views here to get Flask to build url map based on our routes
# Has to be at the bottom after 'app' is defined.
from dashboard import views, models  # noqa: E402
