from datetime import timedelta
from flask_wtf import Form
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.ext.csrf.session import SessionSecureForm
from .models import Study, Site

class SecureForm(SessionSecureForm):
    SECRET_KEY = "you will never guess"
    TIME_LIMIT = timedelta(minutes=20)

class SelectMetricsForm(SecureForm):
    try:
        study_vals = [(study.id, study.name)
                      for study in Study.query.order_by(Study.name).all()]
    except:
        study_vals = []

    study_id = SelectField('Study', choices=study_vals, coerce=int)

    def __init__(self,  *args, **kwargs):
        SecureForm.__init__(self, *args, **kwargs)
        pass
