import os
import logging.config

from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.routing import BaseConverter

from config import (SCHEDULER_ENABLED, SCHEDULER_API_ENABLED, SCHEDULER_USER,
                    SCHEDULER_PASS, TZ_OFFSET, LOGGING_CONFIG)

if SCHEDULER_ENABLED:
    from flask_apscheduler import APScheduler as Scheduler
else:
    from .task_scheduler import RemoteScheduler as Scheduler

logging.config.dictConfig(LOGGING_CONFIG)

db = SQLAlchemy()
migrate = Migrate()
lm = LoginManager()
lm.login_view = 'users.login'
lm.refresh_view = 'users.refresh_login'
mail = Mail()
scheduler = Scheduler()

if SCHEDULER_API_ENABLED:
    # If this instance is acting as a scheduler server + the api should be
    # available for clients, set up authentication here
    @scheduler.authenticate
    def authenticate(auth):
        return (auth['username'] == SCHEDULER_USER
                and auth['password'] == SCHEDULER_PASS)


class RegexConverter(BaseConverter):
    # This adds a 'regex' type for app routes.
    # See: https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing  # noqa: E501
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def connect_db():
    """Allows access to the database models outside of the flask application

    If importing the dashboard app (i.e. not starting the server properly) this
    function should be called once before attempting to use anything from the
    models otherwise you'll get an exception about working outside of an
    app context
    """
    app = create_app()
    context = app.app_context()
    context.push()
    return db


def setup_devel_ext(app):
    """This sets up any development extensions that may be needed
    """
    try:
        from flask_debugtoolbar import DebugToolbarExtension
    except ImportError:
        app.logger.warn("flask-debugtoolbar not installed. Install it for "
                        "extra development server goodness :)")
    else:
        toolbar = DebugToolbarExtension(app)
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    return toolbar


def create_app(config=None):
    app = Flask(__name__)

    if config is None:
        app.config.from_object('config')
    else:
        app.config.from_mapping(config)

    db.init_app(app)
    migrate.init_app(app, db)
    lm.init_app(app)
    mail.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    app.url_map.converters['regex'] = RegexConverter

    from dashboard.blueprints.main import main_bp
    from dashboard.blueprints.users import user_bp
    from dashboard.blueprints.auth import auth_bp
    from dashboard.blueprints.timepoints import time_bp
    from dashboard.blueprints.scans import scan_bp
    from dashboard.blueprints.redcap import rcap_bp
    from dashboard.blueprints.handlers import handler_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(time_bp)
    app.register_blueprint(rcap_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(handler_bp)

    if app.debug and app.env == 'development':
        # Never run this on a production server!
        setup_devel_ext(app)

    return app
