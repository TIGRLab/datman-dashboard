"""
Web forms used in the flask app are defined here.

Forms are defined using the WTForms api via Flask-WTForms extension.
(https://wtforms.readthedocs.io/en/latest/)

This allows us to create HTML forms in python without having to worry about
the html code or CSRF vulnerabilities
"""

from flask_wtf import FlaskForm
from wtforms import (SelectMultipleField, HiddenField, SubmitField,
                     TextAreaField, TextField, BooleanField, RadioField)
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


class SliceTimingForm(FlaskForm):
    timings = TextAreaField('NewTimings',
                            id="new_timings",
                            render_kw={
                                'rows':
                                4,
                                'cols':
                                65,
                                'required':
                                True,
                                'placeholder':
                                "Enter comma " + "separated slice " + "timings"
                            })
    submit = SubmitField('Update', id='submit_timings')


class ScanChecklistForm(FlaskForm):
    comment = TextAreaField('Comment:',
                            id='scan-comment',
                            validators=[DataRequired()],
                            render_kw={
                                'placeholder': 'Add description',
                                'rows': 12,
                                'required': True,
                                'maxlength': '1028'
                            })
    submit = SubmitField('Submit')


class AnalysisForm(FlaskForm):
    name = TextField('Brief name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    software = TextAreaField('Software')


class EmptySessionForm(FlaskForm):
    comment = TextAreaField('Explanation: ',
                            id="missing_comment",
                            validators=[DataRequired()],
                            render_kw={
                                'rows':
                                4,
                                'cols':
                                50,
                                'required':
                                True,
                                'placeholder':
                                'Please describe what ' + 'happened to this ' +
                                'session.',
                                'maxlength':
                                '2048'
                            })


class IncidentalFindingsForm(FlaskForm):
    comment = TextAreaField('Description: ',
                            id='finding-description',
                            validators=[DataRequired()],
                            render_kw={
                                'rows': 4,
                                'cols': 65,
                                'required': True,
                                'placeholder':
                                'Please describe ' + 'the finding'
                            })
    submit = SubmitField('Submit')


class TimepointCommentsForm(FlaskForm):
    comment = TextAreaField(validators=[DataRequired()],
                            render_kw={
                                'rows': 5,
                                'required': True,
                                'placeholder': 'Add new comment'})
    submit = SubmitField('Submit')


class DataDeletionForm(FlaskForm):
    raw_data = BooleanField('Raw Data')
    database_records = BooleanField('Database Records')


class NewIssueForm(FlaskForm):
    title = TextField("Title: ",
                      validators=[DataRequired()],
                      render_kw={'required': True})
    body = TextAreaField("Body: ",
                         validators=[DataRequired()],
                         render_kw={
                             'rows': 4,
                             'cols': 65,
                             'required': True,
                             'placeholder': 'Enter issue here.'
                         })
    submit = SubmitField('Create Issue')
