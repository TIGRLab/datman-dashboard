from datetime import timedelta
from flask import session
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, HiddenField, TextAreaField, TextField, FormField, BooleanField
from wtforms.validators import DataRequired
from models import Study
from wtforms.csrf.session import SessionCSRF


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

    def __init__(self,  *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)


class StudyOverviewForm(FlaskForm):
    readme_txt = TextAreaField(u'README', id='readme_editor')
    study_id = HiddenField()


class ScanForm(FlaskForm):
    bl_comment = TextField(u'Blacklist_comment',
                           validators=[DataRequired()])


class SessionForm(FlaskForm):
    cl_comment = TextField(u'Checklist_comment',
                           validators=[DataRequired()])

class UserForm(FlaskForm):
    user_id = HiddenField()
    realname = TextField(u'realname',
                         validators=[DataRequired()])
    is_admin = BooleanField(u'is_admin', default=False)
    has_phi = BooleanField(u'has_phi', default=False)
    studies = SelectMultipleField(u'studies')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        studies = Study.query.all()
        study_choices = [(str(study.id), study.nickname) for study in studies]
        self.studies.choices = study_choices
