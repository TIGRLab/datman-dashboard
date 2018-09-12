"""
Web forms used in the flask app are defined here
Forms are defined using the WTForms api (https://wtforms.readthedocs.io/en/latest/)
    via Flask-WTForms extension.
This allows us to create HTML forms in python without having to worry about
    the html code.
"""

from flask import session
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, HiddenField, SubmitField, \
        TextAreaField, TextField, FormField, BooleanField, widgets, FieldList, \
        RadioField
from wtforms.compat import iteritems
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

# class MultiCheckboxField(SelectMultipleField):
#     widget = widgets.ListWidget(prefix_label=False)
#     option_widget = widgets.CheckboxInput()

# class StudySelectionForm(FlaskForm):
#     # studies = MultiCheckboxField(u'Study Access')
#
#
#     def __init__(self, *args, **kwargs):
#         FlaskForm.__init__(self, *args, **kwargs)
#         studies = Study.query.all()
#         study_choices = [(study.id, study.id) for study in studies]
#         self.studies.choices = sorted(study_choices)

# class BooleanSubField(BooleanField):
#     """
#     Work around for the fact that BooleanFields in a FormField list get
#     set to 'True' regardless of what default you specify, as
#     explained here: https://github.com/wtforms/wtforms/issues/308
#     """
#     def process_data(self, value):
#         if isinstance(value, BooleanField):
#             self.data = value.data
#         else:
#             self.data = bool(value)
#
# class StudyPermissionsForm(FlaskForm):
#     study_id = TextField('Study: ', render_kw={'readonly': True})
#     user_id = HiddenField()
#     enabled = BooleanSubField('Access enabled')
#     is_admin = BooleanSubField('Admin Access (can delete data + comments): ')
#     primary_contact = BooleanSubField('Primary Contact (usually the PI): ')
#     kimel_contact = BooleanSubField('Kimel Contact (i.e. staff member(s) in ' +
#         'charge of handling this study): ')
#     study_RA = BooleanSubField('Study RA: ')
#     does_qc = BooleanSubField('Does QC: ')



class UserForm(FlaskForm):
    id = HiddenField()
    first_name = TextField(u'First Name: ',
                         validators=[DataRequired()])
    last_name = TextField(u'Last Name: ',
                         validators=[DataRequired()])
    email = TextField(u'Email: ')
    position = TextField(u'Position: ')
    institution = TextField(u'Institution: ')
    phone1 = TextField(u'Phone Number: ')
    phone2 = TextField(u'Alt. Phone Number: ')
    github_name = TextField(u'GitHub Username: ')
    gitlab_name = TextField(u'GitLab Username: ')
    update = SubmitField(label='Update')

class PermissionRadioField(RadioField):

    def __init__(self, *args, **kwargs):
        super(PermissionRadioField, self).__init__(**kwargs)
        self.choices = [(u'False', 'Disabled'), (u'True', 'Enabled')]
        self.default = u'False'

class StudyPermissionsForm(FlaskForm):
    study_id = HiddenField()
    user_id = HiddenField()
    is_admin = PermissionRadioField('Admin Access (can delete data + comments): ')
    primary_contact = PermissionRadioField('Primary Contact (usually the PI): ')
    kimel_contact = PermissionRadioField('Kimel Contact (i.e. staff member(s) in ' +
        'charge of handling this study): ')
    study_RA = PermissionRadioField('Study RA: ')
    does_qc = PermissionRadioField('Does QC: ')
    revoke_access = SubmitField(label='Remove Access')

class UserAdminForm(UserForm):
    dashboard_admin = BooleanField(u'Dashboard Admin: ')
    is_active = BooleanField(u'Active Account: ')
    studies = FieldList(FormField(StudyPermissionsForm))
    add_access = SelectMultipleField('Give Access to Studies: ')
    update_access = SubmitField(label='Give Access')
    revoke_all_access = SubmitField(label='Remove All')


    # def __init__(self, *args, **kwargs):
    #     FlaskForm.__init__(self, *args, **kwargs)
    #     user_studies = obj.studies
    #     for record in user_studies:
    #         permissions = StudyPermissionsForm(obj=record)
    #         self.studies.append_entry(permissions)

    # def populate_obj(self, obj):
    #     for study in obj.studies:
    #         permissions = StudyPermissionsForm(obj=study)
    #         self.studies.append_entry(permissions)
    #     UserForm.populate_obj(self, obj)
        # for name, field in iteritems(self._fields):
        #     if name == 'studies':
        #         continue
        #     field.populate_obj(obj, name)

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
