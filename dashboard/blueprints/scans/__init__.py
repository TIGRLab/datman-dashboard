from flask import Blueprint

scan_bp = Blueprint(
    'scans',
    __name__,
    template_folder='templates',
    url_prefix='/study/<string:study_id>/scan/<int:scan_id>')

from . import views
