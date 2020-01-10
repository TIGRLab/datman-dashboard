from flask import Blueprint

user_bp = Blueprint(
    'users',
    __name__,
    template_folder='templates',
    url_prefix='/user')

from . import views
