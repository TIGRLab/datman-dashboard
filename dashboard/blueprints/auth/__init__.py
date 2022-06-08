from flask import Blueprint

auth_bp = Blueprint('auth', __name__)


def register_bp(app):
    app.register_blueprint(auth_bp)
    return app


from . import views
