from flask import Blueprint

handler_bp = Blueprint('handlers', __name__, template_folder='templates')


def register_bp(app):
    app.register_blueprint(handler_bp)
    return app


from . import views
