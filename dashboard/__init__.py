"""Setup and initialization for the QC Dashboard.
"""

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
        """Set authentication credentials for the scheduler server.

        All client schedulers must authenticate with a username and password
        that matches the ones provided.

        Args:
            auth (:obj:`dict`): A dictionary containing the keys 'username' and
                'password'. Clients wishing to use the API must match the two
                values provided.

        Returns:
            bool: True if user provided matching credentials, False otherwise.
        """
        return (auth['username'] == SCHEDULER_USER
                and auth['password'] == SCHEDULER_PASS)


class RegexConverter(BaseConverter):
    """A 'regex' type for URL routes.

    For whatever reason Flask (as of this writing) does not appear to have a
    built-in way to allow regular expressions in URL routes. RegexConverter
    adds this capability. For more info see
    `this post. <https://stackoverflow.com/questions/5870188/does-flask-support-regular-expressions-in-its-url-routing>`_

    Example:
        .. code-block:: python

            @app.route('/someroute/<regex("*.png"):varname>')
            def some_view(varname):
                ...

        This would add a URL endpoint for the pattern ``/someroute/*.png``. The
        part of the URL that matches the regex will be passed in to the view
        without the prefix. e.g. accessing the URL '/someroute/my_picture.png'
        would set varname to 'my_picture.png'
    """  # noqa: E501

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def connect_db():
    """Push an application context to allow external access to database models.

    Anything that uses a flask extension, or accesses the app config, needs to
    operate inside of an
    `application context. <https://flask.palletsprojects.com/en/1.1.x/appcontext/>`_
    This function can be called to push the context.
    """  # noqa: E501
    app = create_app()
    context = app.app_context()
    context.push()
    return db


def setup_devel_ext(app):
    """Set up extensions only used within development environments.
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
    """Generate an application instance from the given configuration.

    This will load the application configuration, initialize all extensions,
    and register all blueprints.
    """
    app = Flask(__name__)
    app.jinja_env.add_extension('jinja2.ext.do')

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
    try:
        scheduler._scheduler.app = app
    except AttributeError:
        # Unlike APScheduler, RemoteScheduler doesnt have _scheduler and
        # doesnt need app access. Ignore it.
        pass

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
