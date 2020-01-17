from flask import Blueprint

handler_bp = Blueprint('handlers', __name__, template_folder='templates')

from . import views
