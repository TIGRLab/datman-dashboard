"""
Web forms used in the flask app are defined here.

Forms are defined using the WTForms api via Flask-WTForms extension.
(https://wtforms.readthedocs.io/en/latest/)

This allows us to create HTML forms in python without having to worry about
the html code or CSRF vulnerabilities
"""

from flask_wtf import FlaskForm
from wtforms import (SelectMultipleField, HiddenField, SubmitField,
                     TextAreaField, TextField)
from wtforms.validators import DataRequired


class SelectMetricsForm(FlaskForm):
    study_vals = []
    site_vals = []
    session_vals = []
    scan_vals = []
    scantype_vals = []
    metrictype_vals = []

    study_id = SelectMultipleField('Study', coerce=int)
    site_id = SelectMultipleField('Site', coerce=int)
    session_id = SelectMultipleField('Session', coerce=int)
    scan_id = SelectMultipleField('Scan', coerce=int)
    scantype_id = SelectMultipleField('Scan type', coerce=int)
    metrictype_id = SelectMultipleField('Metric type', coerce=int)
    query_complete = HiddenField(default=False)
    is_phantom = HiddenField(default=False)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)


class StudyOverviewForm(FlaskForm):
    readme_txt = TextAreaField('README', id='readme_editor')
    study_id = HiddenField()


class AnalysisForm(FlaskForm):
    name = TextField('Brief name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    software = TextAreaField('Software')
