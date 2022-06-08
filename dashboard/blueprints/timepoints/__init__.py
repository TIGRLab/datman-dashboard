from flask import Blueprint

time_bp = Blueprint(
    'timepoints',
    __name__,
    template_folder='templates',
    url_prefix='/study/<string:study_id>/timepoint/<string:timepoint_id>'
)

ajax_bp = Blueprint(
    'ajax_timepoints',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/timepoint'
)


def register_bp(app):
    app.register_blueprint(time_bp)
    return app


from . import views
