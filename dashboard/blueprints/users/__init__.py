from flask import Blueprint

user_bp = Blueprint(
    'users',
    __name__,
    template_folder='templates',
    url_prefix='/user')


def register_bp(app):
    app.register_blueprint(user_bp)
    return app


from . import views
