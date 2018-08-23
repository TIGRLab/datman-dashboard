"""
Web forms used in the flask app are defined here
Forms are defined using the WTForms api (https://wtforms.readthedocs.io/en/latest/)
    via Flask-WTForms extension.
This allows us to create HTML forms in python without having to worry about
    the html code.
"""

from flask import session
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, HiddenField, SubmitField, FieldList
from wtforms import TextAreaField, TextField, FormField, BooleanField, RadioField, IntegerField
from wtforms import Form as BaseForm
from wtforms.validators import DataRequired, InputRequired, NoneOf, Length, Optional, NumberRange, Email, AnyOf
from models import Study, Analysis, ScanType, Site, Person, User
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


class ScanTypeForm(BaseForm):
    scantype_name = SelectField(u'Select Scantype',
        validators=[
            InputRequired(u'Required Field'),
        ])
    patterns = StringField(u'Patterns',
        validators=[
            Optional()
        ])
    count = IntegerField(u'Count',
        validators=[
            Optional(),
            NumberRange(min=0, message='Count must not be below 0')
        ])

    def __init__(self, *args, **kwargs):
        BaseForm.__init__(self, *args, **kwargs)
        scantypes = ScanType.query.all()
        scantype_choices = [('', '')] + [(str(scantype.id), str(scantype.name)) for scantype in scantypes]
        self.scantype_name.choices = sorted(scantype_choices, key=lambda x: x[1])

class NewScantypeForm(FlaskForm):
    new_scantype_name = StringField(u'New Scantype Name',
        validators=[
            NoneOf([], message=u'Scantype already exists'),
            InputRequired(u'Required Field'),
            Length(max=64, message=u'Length must be less than 65')
        ]
    )
    submit_scantype = SubmitField(u'Add New Scantype')

class SiteForm(BaseForm):
    site_name = SelectField(u'Select Site', default=' ', choices=[' '],
        validators=[
            InputRequired(u'Required Field'),
        ])
    site_tags =StringField(u'Site Tags',
        validators=[
            Optional()
        ])
    xnat_archive = StringField(u'XNAT_Archive',
        validators=[
            Optional()
        ])
    scantypes = FieldList(FormField(ScanTypeForm, u'Site Scantypes'), min_entries=1)
    ftpserver = StringField(u'FTPSERVER',
        description='Overrides the default server usually set ing the site wide config',
        validators=[
            Optional()
        ])
    ftpport = StringField(u'FTPPORT',
        description='Allows a site to use a non-standard port for the sftp server',
        validators=[
            Optional()
        ])
    mrftppass = StringField(u'MRFTPPASS',
        description='Should be set to the name of the file in the metadata folder that will hold this site\'s sftp account password',
        validators=[
            Optional()
        ])
    mruser = StringField(u'MRUSER',
        description='Overrides the default MRUSER for the study',
        validators=[
            Optional()
        ])
    mrfolder = StringField(u'MRFOLDER',
        description='Overrides default MRFOLDER for the study',
        validators=[
            Optional()
        ])
    xnat_source = StringField(u'XNAT Source',
        description='The URL for the remote XNAT server to pull from',
        validators=[
            Optional()
        ])
    xnat_source_archive = StringField(u'XNAT Source Archive',
        description='The Project ID on the XNAT server that holds this site\'s data',
        validators=[
            Optional()
        ])
    xnat_source_credentials = StringField(u'XNAT Source Credentials',
        description='The name of the text file in the metadata forlder that will hold the username and password on separate lines (in that order)',
        validators=[
            Optional()
        ])
    redcap_api = StringField(u'REDCAP API',
        description='Server that hosts the \'Scan Completed\' surveys (or any other surveys that need to be pulled in',
        validators=[
            Optional()
        ])

    def __init__(self, *args, **kwargs):
        BaseForm.__init__(self, *args, **kwargs)
        sites = Site.query.all()
        site_choices = [('', '')] + [(str(site.id), site.name) for site in sites]
        self.site_name.choices = sorted(site_choices, key=lambda x: x[1])

class NewSiteForm(FlaskForm):
    new_site_name = StringField(u'New Site Name',
        validators=[
            NoneOf([], message=u'Site already exists'),
            InputRequired(u'Required Field'),
            Length(max=64, message=u'Length must be less than 65')
        ]
    )
    submit_site = SubmitField(u'Add New Site')

class StudyForm(FlaskForm):
    nickname = StringField(u'Nickname',
        validators=[
            NoneOf([], message=u'Nickname already exists'),
            InputRequired(u'Required Field'),
            Length(max=12, message=u'Length must be less than 13')
        ])
    study_name = StringField(u'Name',
        validators=[
            InputRequired(u'Required Field'),
            Length(max=1024, message=u'Length must be less than 1025')
        ])
    description = TextAreaField(u'Description',
        validators=[
            Optional(),
            Length(max=1024, message=u'Length must be less than 1025')
        ])
    people = SelectField(u'Primary Contact')
    users = SelectMultipleField(u'Users')
    sites = FieldList(FormField(SiteForm), u'Sites', min_entries=1)
    submit_study = SubmitField(u'Add Study')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        sites = Site.query.all()
        people = Person.query.all()
        person_choices = [('', '')] + [(str(person.id), person.name) for person in people]
        self.people.choices = sorted(person_choices, key=lambda x: x[1])
        users = User.query.all()
        user_choices = [(str(user.id), user.realname) for user in users]
        self.users.choices = user_choices

class PersonForm(FlaskForm):
    person_name = StringField(u'Name',
        validators=[
            NoneOf([], message=u'PI already exists'),
            InputRequired(u'Required Field'),
            Length(max=64, message=u'Length must be less than 65')
        ])
    role = StringField(u'Role',
        validators=[
            Optional(),
            Length(max=64, message=u'Length must be less than 65')
        ])
    person_email = StringField(u'Email',
        validators=[
            Optional(),
            Email(message='Email is not valid'),
            Length(max=255, message=u'Length must be less than 256')
        ])
    phone1 = StringField(u'Phone1',
        validators=[
            Optional(),
            Length(max=20, message=u'Length must be less than 21')
        ])
    phone2 = StringField(u'Phone2',
        validators=[
            Optional(),
            Length(max=20, message=u'Length must be less than 21')
        ])
    submit_person = SubmitField(u'Add PI')

class AddUserForm(FlaskForm):
    realname = StringField(u'Full Name',
        validators=[
            NoneOf([], message=u'User already exists'),
            InputRequired(u'Required Field'),
            Length(max=64, message=u'Length must be less than 65')
        ])
    username = StringField(u'Username',
        validators=[
            NoneOf([], message=u'Username already exists'),
            InputRequired(u'Required Field'),
            Length(max=64, message=u'Length must be less than 65')
        ])
    user_email = StringField(u'Email',
        validators=[
            Optional(),
            Email(message='Email is not valid'),
            Length(max=120, message=u'Length must be less than 121')
        ])
    is_admin = BooleanField(u'Is Admin')
    has_phi = BooleanField(u'Has Phi')
    submit_user = SubmitField(u'Add User')
