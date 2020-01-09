from flask import Blueprint

user_bp = Blueprint('users', __name__, template_folder='templates')

from . import views
