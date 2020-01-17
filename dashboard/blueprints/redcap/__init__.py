from flask import Blueprint

rcap_bp = Blueprint('redcap', __name__)

from . import views
