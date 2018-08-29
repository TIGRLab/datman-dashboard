"""
Object definition file for dashboard app
Each class defines a table in the database.

Of interest, check out sessions.validate_comment() and scan.validate_comment()
The @validates decorator ensures this is run before the checklist comment
    field can be updated in the database. This is what ensures the filesystem
    checklist.csv is in sync with the database.
"""
import logging
import datetime

from flask_login import UserMixin
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint

from dashboard import db


logger = logging.getLogger(__name__)

################################################################################
# Association tables (i.e. basic many to many relationships)

study_scantype_table = db.Table('study_scantypes',
        db.Column('study', db.String(32), db.ForeignKey('studies.id'),
                nullable=False),
        db.Column('scantype', db.String(64), db.ForeignKey('scantypes.tag'),
                nullable=False))

study_sessions_table = db.Table('study_sessions',
        db.Column('study', db.String(32), db.ForeignKey('studies.id'),
                nullable=False),
        db.Column('timepoint', db.String(64), nullable=False),
        db.Column('session', db.Integer, nullable=False),
        ForeignKeyConstraint(('timepoint', 'session'),
                ('sessions.name', 'sessions.num')),
        UniqueConstraint('study', 'timepoint', 'session'))

################################################################################
# Plain entities

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, primary_key=True)
    first_name = db.Column('first_name', db.String(64), nullable=False)
    last_name = db.Column('last_name', db.String(64), nullable=False)
    email = db.Column('email', db.String(256))
    position = db.Column('position', db.String(64))
    institution = db.Column('institution', db.String(128))
    phone1 = db.Column('phone1', db.String(20))
    phone2 = db.Column('phone2', db.String(20))
    github_name = db.Column('github_username', db.String(64))
    gitlab_name = db.Column('gitlab_username', db.String(64))
    is_staff = db.Column('kimel_staff', db.Boolean, default=False)
    is_active = db.Column('account_active', db.Boolean, default=False)

    studies = db.relationship('StudyUser', back_populates='user')
    incidental_findings = db.relationship('IncidentalFinding')
    blacklist_comments = db.relationship('ScanBlacklist')
    timepoint_comments = db.relationship('TimepointComment')
    analysis_comments = db.relationship('AnalysisComment')
    sessions_reviewed = db.relationship('Session')

    def __init__(self, first, last, email=None, position=None, institution=None,
            phone1=None, phone2=None, github_name=None, gitlab_name=None,
            is_staff=False, account_active=False):
        self.first_name = first
        self.last_name = last
        self.email = email
        self.position = position
        self.institution = institution
        self.phone1 = phone1
        self.phone2 = phone2
        self.github_name = github_name
        self.gitlab_name = gitlab_name
        self.is_staff = is_staff
        self.account_active = account_active

    def get_studies(self):
        """
        Get a list of Study objects that this user has access to.
        """
        if self.is_staff:
            studies = Study.query.all()
        else:
            studies = [study_user.study for study_user in self.studies]
        return studies

    def has_study_access(self, study):
        """
        Check if user has access to a specific study.
        """
        if self.is_staff:
            return True
        if isinstance(study, Study):
            study = Study.id
        return study in [su.study_id for su in self.studies]

    def __repr__(self):
        return "<User {}: {} {}>".format(self.id, self.first_name,
                self.last_name)


class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column('id', db.String(32), primary_key=True)
    code = db.Column('study_code', db.String(32))
    name = db.Column('name', db.String(1024))
    description = db.Column('description', db.Text)

    users = db.relationship('StudyUser', back_populates='study')
    sites = db.relationship('StudySite', back_populates='study')
    sessions = db.relationship('Session', secondary=study_sessions_table,
            back_populates='studies')
    scantypes = db.relationship('Scantype', secondary=study_scantype_table,
            back_populates='studies')

    def __init__(self, study_id, code=None, full_name=None, description=None):
        self.id = study_id
        self.code = code
        self.full_name = full_name
        self.description = description

    def new_sessions(self):
        need_qc = [session for session in self.sessions
                if not session.timepoint.is_phantom and not session.signed_off]
        return len(need_qc)

    def get_valid_metric_names(self):
        """
        Return a list of metric names with duplicates removed.

        TODO: This entire method needs to be updated to be less hard-coded. We
        should get the 'type' of scan from our config file 'qc_type' field
        instead (and store it in the database). For now I just got it
        working with the new schema - Dawn
        """
        valid_fmri_scantypes = ['IMI', 'RST', 'EMP', 'OBS', 'SPRL', 'VN-SPRL']
        names = []
        for scantype in self.scantypes:
            for metrictype in scantype.metrictypes:
                if scantype.tag.startswith('DTI'):
                    names.append(('DTI', metrictype.name))
                elif scantype.tag in valid_fmri_scantypes:
                    names.append(('FMRI', metrictype.name))
                elif scantype.tag == 'T1':
                    names.append(('T1', metrictype.name))

        names = sorted(set(names))
        return(names)

    def session_count(self, type=''):
        if type.lower() == 'human':
            sessions = [sess for sess in self.sessions
                    if not sess.timepoint.is_phantom]
        elif type.lower() == 'phantom':
            sessions = [sess for sess in self.sessions
                    if sess.timepoint.is_phantom]
        else:
            sessions = self.sessions
        return len(sessions)

    def outstanding_issues(self):
        session_list = []
        for session in self.sessions:
            if (not session.is_qcd() or
                    self.needs_redcap_survey(session) or
                    session.expecting_scans()):
                session_list.append(session)
        return session_list

    def get_primary_contacts(self):
        contacts = [study_user.user for study_user in self.users
                if study_user.primary_contact]
        return contacts

    def needs_redcap_survey(self, session):
        if session.timepoint.is_phantom:
            return False
        cur_site = [study_site for study_site in self.sites
                if study_site.site_id == session.timepoint.site_id][0]
        if cur_site.uses_redcap:
            return not session.redcap_record_id
        return False

    def __repr__(self):
        return "<Study {}>".format(self.id)


class Site(db.Model):
    __tablename__ = 'sites'

    name = db.Column('name', db.String(32), primary_key=True)
    description = db.Column('description', db.Text)

    studies = db.relationship('StudySite', back_populates='site')
    timepoints = db.relationship('Timepoint')

    def __init__(self, site_name, description=None):
        self.name = site_name
        self.description = description

    def __repr__(self):
        return "<Site {}>".format(self.name)


class Timepoint(db.Model):
    __tablename__ = 'timepoints'

    name = db.Column('name', db.String(64), primary_key=True)
    site_id = db.Column('site', db.String(32), db.ForeignKey('sites.name'),
            nullable=False)
    is_phantom = db.Column('is_phantom', db.Boolean, nullable=False,
            default=False)
    github_issue = db.Column('github_issue', db.Integer)
    gitlab_issue = db.Column('gitlab_issue', db.Integer)
    last_qc_repeat_generated =  db.Column('last_qc_generated', db.Integer,
            nullable=False, default=1)

    site = db.relationship('Site', uselist=False, back_populates='timepoints')
    sessions = db.relationship('Session')
    comments = db.relationship('TimepointComment')
    incidental_findings = db.relationship('IncidentalFinding')

    def __init__(self, t_id, site, is_phantom=False, github_issue=None,
            gitlab_issue=None):
        self.id = t_id
        self.site = site
        self.is_phantom = is_phantom
        self.github_issue = github_issue
        self.gitlab_issue = gitlab_issue

    def is_qcd(self):
        if self.is_phantom:
            return True
        return all(sess.is_qcd() for sess in self.sessions)

    def __repr__(self):
        return "<Timepoint {}>".format(self.id)


class Session(db.Model):
    __tablename__ = 'sessions'

    name = db.Column('name', db.String(64), db.ForeignKey('timepoints.name'),
            primary_key=True)
    num = db.Column('num', db.Integer, primary_key=True)
    date = db.Column('date', db.DateTime)
    signed_off = db.Column('signed_off', db.Boolean, default=False)
    reviewer_id = db.Column('reviewer', db.Integer, db.ForeignKey('users.id'))
    review_date = db.Column('review_date', db.DateTime(timezone=True))
    redcap_record_id = db.Column('redcap_record', db.Integer,
            db.ForeignKey('redcap_records.id'))

    timepoint = db.relationship('Timepoint', uselist=False,
            back_populates='sessions')
    scans = db.relationship('Scan')
    studies = db.relationship('Study', secondary=study_sessions_table,
            back_populates='sessions')
    reviewer = db.relationship('User', uselist=False,
            back_populates='sessions_reviewed')
    redcap_record = db.relationship('RedcapRecord', uselist=False,
            back_populates='sessions')

    def __init__(self, name, num, date=None, signed_off=False, reviewer=None,
            review_date=None, redcap_record=None):
        self.name = name
        self.num = num
        self.date = date
        self.signed_off = signed_off
        self.reviewer = reviewer
        self.review_date = review_date
        self.redcap_record = redcap_record

    def is_qcd(self):
        if self.timepoint.is_phantom:
            return True
        return self.signed_off

    def expecting_scans(self):
        return (self.redcap_record and not self.scans)

    def __repr__(self):
        return "<Session {}, {}>".format(self.name, self.num)


class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(128), nullable=False)
    timepoint = db.Column('timepoint', db.String(64), nullable=False)
    repeat = db.Column('session', db.Integer, nullable=False)
    series = db.Column('series', db.Integer, nullable=False)
    tag = db.Column('tag', db.String(64), db.ForeignKey('scantypes.tag'),
            nullable=False)
    description = db.Column('description', db.String(128))
    # If a scan is a link, this will hold the id of the scan the link points to
    source_id = db.Column('source_data', db.Integer, db.ForeignKey(id))

    # If a scan has any links pointing to it, this will hold a list of the
    # IDs for these scans
    other_ids = db.relationship("Scan")
    session = db.relationship('Session', uselist=False, back_populates='scans')
    scantype = db.relationship('Scantype', uselist=False, back_populates='scans')
    analysis_comments = db.relationship("AnalysisComment")
    metric_values = db.relationship('MetricValue', cascade="all, delete-orphan")

    __table_args__ = (ForeignKeyConstraint(['timepoint', 'session'],
            ['sessions.name', 'sessions.num']),
            UniqueConstraint(timepoint, repeat, series))

    def __init__(self, name, timepoint, repeat, series, tag, description=None,
            source_id=None):
        self.name = name
        self.timepoint = timepoint
        self.repeat = repeat
        self.series = series
        self.tag = tag
        self.description = description
        self.source_id = source_id

    def __repr__(self):
        if self.source_id:
            repr = "<Scan {}: {} link to scan {}>".format(self.id, self.name,
                    self.source_id)
        else:
            repr = "<Scan {}: {}>".format(self.id, self.name)
        return repr


class Scantype(db.Model):
    __tablename__ = 'scantypes'

    tag = db.Column('tag', db.String(64), primary_key=True)

    scans = db.relationship('Scan', back_populates='scantype')
    studies = db.relationship('Study', secondary=study_scantype_table,
            back_populates='scantypes')
    metrictypes = db.relationship('Metrictype', back_populates='scantype')

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "<Scantype {}>".format(self.tag)


class TimepointComment(db.Model):
    __tablename__ = 'timepoint_comments'

    id = db.Column('id', db.Integer, primary_key=True)
    timepoint_id = db.Column('timepoint', db.String(64),
            db.ForeignKey('timepoints.name'), nullable=False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    timestamp = db.Column('comment_timestamp', db.DateTime(timezone=True),
            nullable=False)
    comment = db.Column('comment', db.Text, nullable=False)

    user = db.relationship('User', uselist=False,
            back_populates='timepoint_comments')
    timepoint = db.relationship('Timepoint', uselist=False,
            back_populates='comments')

    def __init__(self, timepoint_id, user_id, comment):
        self.timepoint_id = timepoint_id
        self.user_id = user_id
        self.comment = comment
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return "<TimepointComment for {} by user {}>".format(self.timepoint_id,
                self.user_id)


class ScanBlacklist(db.Model):
    __tablename__ = 'scan_blacklist'

    id = db.Column('id', db.Integer, primary_key=True)
    # Not a foreign key so blacklist entries can be retained even if a scan is
    # deleted temporarily
    scan_name = db.Column('scan_name', db.String(128), nullable=False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    timestamp = db.Column('comment_timestamp', db.DateTime(timezone=True),
            nullable=False)
    comment = db.Column('comment', db.Text, nullable=False)

    user = db.relationship('User', uselist=False,
            back_populates='blacklist_comments')

    __table_args__ = (UniqueConstraint(scan_name),)

    def __init__(self, scan_name, user_id, comment):
        self.scan_name = scan_name
        self.user_id = user_id
        self.comment = comment
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return "<ScanBlacklist for {} by user {}>".format(self.scan_name,
                self.user_id)


class RedcapRecord(db.Model):
    __tablename__ = 'redcap_records'

    id = db.Column('id', db.Integer, primary_key=True)
    record = db.Column('record', db.String(256), nullable=False)
    project = db.Column('project_id', db.Integer, nullable=False)
    url = db.Column('url', db.String(1024), nullable=False)
    instrument = db.Column('instrument', db.String(1024))
    date = db.Column('entry_date', db.Date)
    user = db.Column('redcap_user', db.Integer)
    comment = db.Column('comment', db.Text)
    redcap_version = db.Column('redcap_version', db.String(10), default='7.4.2')
    event_id = db.Column('event_id', db.Integer)

    sessions = db.relationship('Session', back_populates='redcap_record')

    __table_args__ = (UniqueConstraint(record, project, url),)

    def __init__(self, record, project, url):
        self.record = record
        self.project = project
        self.url = url

    def __repr__(self):
        return "<RedcapRecord {}: record {} project {} url {}>".format(self.id,
                self.record, self.project, self.url)


class Analysis(db.Model):
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(4096), nullable=False)
    software = db.Column(db.String(4096))

    analysis_comments = db.relationship('AnalysisComment')

    def __repr__(self):
        return('<Analysis {}: {}>'.format(self.id, self.name))

class Metrictype(db.Model):
    __tablename__ = 'metrictypes'

    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(64), nullable=False)
    scantype_id = db.Column('scantype', db.String(64),
            db.ForeignKey('scantypes.tag'), nullable=False)

    scantype = db.relationship('Scantype', back_populates='metrictypes')
    metric_values = db.relationship('MetricValue')

    def __repr__(self):
        return('<MetricType {}>'.format(self.name))


################################################################################
# Association Objects (i.e. many to many relationships with attributes/columns
# of their own).

class StudyUser(db.Model):
    __tablename__ = 'study_users'

    study_id = db.Column('study_id', db.String(32), db.ForeignKey('studies.id'),
            nullable=False, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False, primary_key=True)
    phi_access = db.Column('phi_access', db.Boolean, default=False)
    is_admin = db.Column('is_admin', db.Boolean, default=False)
    primary_contact = db.Column('primary_contact', db.Boolean, default=False)
    kimel_contact = db.Column('kimel_contact', db.Boolean, default=False)
    study_RA = db.Column('study_ra', db.Boolean, default=False)
    does_qc = db.Column('does_qc', db.Boolean, default=False)

    study = db.relationship('Study', back_populates='users')
    user = db.relationship('User', back_populates='studies')

    def __init__(self, study_id, user_id, phi=False, admin=False,
            is_primary_contact=False, is_kimel_contact=False, is_study_RA=False,
            does_qc=False):
        self.study_id = study_id
        self.user_id = user_id
        self.phi_access = phi
        self.is_admin = admin
        self.primary_contact = is_primary_contact
        self.kimel_contact = is_kimel_contact
        self.study_RA = is_study_RA
        self.does_qc = does_qc

    def __repr__(self):
        return "<StudyUser {} User: {}>".format(self.study_id,
                self.user_id)


class StudySite(db.Model):
    __tablename__ = 'study_site'

    study_id = db.Column('study', db.String(32), db.ForeignKey('studies.id'),
            primary_key=True)
    site_id = db.Column('site', db.String(32), db.ForeignKey('sites.name'),
            primary_key=True)
    uses_redcap = db.Column('uses_redcap', db.Boolean, default=False)

    site = db.relationship('Site', back_populates='studies')
    study = db.relationship('Study', back_populates='sites')

    def __init__(self, study_id, site_id, uses_redcap=False):
        self.study_id = study_id
        self.site_id = site_id
        self.uses_redcap = uses_redcap

    def __repr__(self):
        return "<StudySite {} - {}>".format(self.study_id, self.site_id)

class AnalysisComment(db.Model):
    __tablename__ = 'analysis_comments'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'),
            nullable=False)
    excluded = db.Column(db.Boolean, default=False)
    comment = db.Column(db.String(4096), nullable=False)

    scan = db.relationship('Scan', uselist=False,
            back_populates="analysis_comments")
    analysis = db.relationship('Analysis', uselist=False,
            back_populates="analysis_comments")
    user = db.relationship('User', uselist=False,
            back_populates="analysis_comments")

    def __repr__(self):
        return "<ScanComment {}: Analysis {} comment on scan {} by user {}>".format(
                self.id, self.analysis_id, self.scan_id, self.user_id)

class IncidentalFinding(db.Model):
    __tablename__ = 'incidental_findings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    timepoint_id = db.Column(db.String(64), db.ForeignKey('timepoints.name'),
            nullable=False)
    description = db.Column(db.Text)

    session = db.relationship('Timepoint', uselist=False,
            back_populates="incidental_findings")
    user = db.relationship('User', uselist=False,
            back_populates="incidental_findings")

    def __repr__(self):
        return "<IncidentalFinding {} for {} found by User {}>".format(
                self.id, self.timepoint_id, self.user_id)

class MetricValue(db.Model):
    __tablename__ = 'scan_metrics'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    metrictype_id = db.Column(db.Integer, db.ForeignKey('metrictypes.id'),
            nullable=False)
    _value = db.Column('value', db.Text)

    scan = db.relationship('Scan', back_populates="metric_values")
    metrictype = db.relationship('Metrictype', back_populates="metric_values")

    @property
    def value(self):
        """Returns the value field from the database.
        The value is stored as a string.
        If the value contains '::' character this will convert it to a list,
        otherwise it will attempt to cast to Float.
        Failing that the value is returned as a string.
        """
        if self._value is None:
            return(None)
        value = self._value.split('::')
        try:
            value = [float(v) for v in value]
        except ValueError:
            return(''.join(value))
        if len(value) == 1:
            return(value[0])
        else:
            return(value)

    @value.setter
    def value(self, value, delimiter=None):
        """Stores the value in the database as a string.
        If the delimiter is specified any characters matching delimiter are
        replaced with '::' for storage.
        Keyword arguments:
        [delimiter] -- optional character string that is replaced by '::' for
            database storage.
        """
        if delimiter is not None:
            try:
                value = value.replace(delimiter, '::')
            except AttributeError:
                pass
        self._value = str(value)

    def __repr__(self):
        return('<Scan {}: Metric {}: Value {}>'.format(self.scan.name,
                self.metrictype.name, self.value))
