from flask import Blueprint

checklist_bp = Blueprint(
    "qc_search",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/qc-reviews")


def register_bp(app):
    app.register_blueprint(checklist_bp)
    return app


from . import views
