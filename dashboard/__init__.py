from flask import Flask, g
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.routing import BaseConverter

from config import (SCHEDULER_ENABLED, SCHEDULER_API_ENABLED, SCHEDULER_USER,
                    SCHEDULER_PASS, SCHEDULER_SERVER_URL, TZ_OFFSET,
                    GITHUB_OWNER, GITHUB_REPO, SENDER, ADMINS, DASH_SUPPORT)


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
    models.
    """
    app = create_app()
    context = app.app_context()
    context.push()
    return db


db = SQLAlchemy()
migrate = Migrate()
lm = LoginManager()
lm.login_view = 'users.login'
lm.refresh_view = 'users.refresh_login'
mail = Mail()

if SCHEDULER_ENABLED:
    from flask_apscheduler import APScheduler
    scheduler = APScheduler()
    if SCHEDULER_API_ENABLED:
        @scheduler.authenticate
        def authenticate(auth):
            return (auth['username'] == SCHEDULER_USER
                    and auth['password'] == SCHEDULER_PASS)
else:
    from .task_scheduler import RemoteScheduler
    scheduler = RemoteScheduler(SCHEDULER_USER, SCHEDULER_PASS,
                                SCHEDULER_SERVER_URL)


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

    from dashboard.main import main_bp
    from dashboard.users import user_bp
    from dashboard.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(auth_bp)

    return app
