from flask import render_template, jsonify, request
from flask_login import current_user

from dashboard import db
from . import handler_bp
from ...exceptions import InvalidUsage


@handler_bp.app_errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@handler_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@handler_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
