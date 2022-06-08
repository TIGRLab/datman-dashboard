from flask import Blueprint

main_bp = Blueprint('main', __name__)


def register_bp(app):
    app.register_blueprint(main_bp)
    return app


from . import views
