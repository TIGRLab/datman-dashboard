from flask import Blueprint

rcap_bp = Blueprint('redcap', __name__)


def register_bp(app):
    app.register_blueprint(rcap_bp)
    return app


from . import views
