"""
Web forms used in the flask app are defined here
Forms are defined using the WTForms api (https://wtforms.readthedocs.io/en/latest/)
    via Flask-WTForms extension.
This allows us to create HTML forms in python without having to worry about
    the html code.
"""

from flask import session
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, HiddenField, SubmitField
from wtforms import TextAreaField, TextField, FormField, BooleanField
from wtforms.validators import DataRequired, Email
from models import Study, Analysis
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


class ScanBlacklistForm(FlaskForm):
    scan_id = HiddenField(id="scan_id")
    bl_comment = TextField(u'Enter the reason for blacklisting: ',
                           id="bl_comment",
                           validators=[DataRequired()])
    submit = SubmitField('Submit')
    delete = SubmitField('Delete Entry')

class SessionForm(FlaskForm):
    cl_comment = TextAreaField(u'Checklist_comment',
                           validators=[DataRequired()])


class UserForm(FlaskForm):
    user_id = HiddenField()
    first_name = TextField(u'First Name: ',
                         validators=[DataRequired()])
    last_name = TextField(u'Last Name: ',
                         validators=[DataRequired()])
    # email = TextField(u'Email', validators=[DataRequired(), Email()])
    # position = TextField(u'Position')
    # institution = TextField(u'Institution')
    # phone1 = TextField(u'Phone Number')
    # phone2 = TextField(u'Alt. Phone Number')
    # github_name = TextField(u'GitHub Username')
    # gitlab_name = TextField(u'GitLab Username')
    # is_staff = BooleanField(u'Kimel Staff', default=False)
    # is_active = BooleanField(u'Active Account', default=False)
    # has_phi = BooleanField(u'PHI Access', default=False)
    studies = SelectMultipleField(u'Studies')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        studies = Study.query.all()
        self.studies.choices = [(study.id, study.name) for study in studies]


class AnalysisForm(FlaskForm):
    name = TextField(u'Brief name',
                     validators=[DataRequired()])
    description = TextAreaField(u'Description',
                            validators=[DataRequired()])
    software = TextAreaField(u'Software')


class ScanCommentForm(FlaskForm):
    scan_id = HiddenField(id="scan_id")
    user_id = HiddenField(id="user_id")
    analyses = SelectField(u'Analysis used:', id="analysis")
    excluded = BooleanField(u'Was excluded:', id="excluded", default=False)
    comment = TextField(u'Comment',
                        id="comment",
                        validators=[DataRequired()])
    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        analyses = Analysis.query.all()
        analysis_choices = [(str(analysis.id), analysis.name)
                            for analysis in analyses]
        self.analyses.choices = analysis_choices
