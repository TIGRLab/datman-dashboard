from datetime import timedelta
from flask import session
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired

from wtforms.csrf.session import SessionCSRF

<<<<<<< HEAD

class SelectMetricsForm(FlaskForm):
    study_vals = []
    site_vals = []
    session_vals = []
    scan_vals = []
    scantype_vals = []
    metrictype_vals = []

=======

class SelectMetricsForm(Form):
    study_vals = []
    site_vals = []
    session_vals = []
    scan_vals = []
    scantype_vals = []
    metrictype_vals = []

>>>>>>> 364ddc6ce608b5d27fc7b1384e54d542b1618329
    study_id = SelectMultipleField('Study', coerce=int)
    site_id = SelectMultipleField('Site', coerce=int)
    session_id = SelectMultipleField('Session', coerce=int)
    scan_id = SelectMultipleField('Scan', coerce=int)
    scantype_id = SelectMultipleField('Scan type', coerce=int)
    metrictype_id = SelectMultipleField('Metric type', coerce=int)
    query_complete = HiddenField(default=False)

    def __init__(self,  *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
