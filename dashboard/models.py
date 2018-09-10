"""
Object definition file for dashboard app
Each class defines a table in the database.

Of interest, check out sessions.validate_comment() and scan.validate_comment()
The @validates decorator ensures this is run before the checklist comment
    field can be updated in the database. This is what ensures the filesystem
    checklist.csv is in sync with the database.
"""
import logging

from flask_login import UserMixin
from sqlalchemy import and_, exists, func
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection

from dashboard import db


logger = logging.getLogger(__name__)

################################################################################
# Association tables (i.e. basic many to many relationships)

study_scantype_table = db.Table('study_scantypes',
        db.Column('study', db.String(32), db.ForeignKey('studies.id'),
                nullable=False),
        db.Column('scantype', db.String(64), db.ForeignKey('scantypes.tag'),
                nullable=False))

study_timepoints_table = db.Table('study_timepoints',
        db.Column('study', db.String(32), db.ForeignKey('studies.id'),
                nullable=False),
        db.Column('timepoint', db.String(64), db.ForeignKey('timepoints.name'),
                nullable=False),
        UniqueConstraint('study', 'timepoint'))

session_redcap_table = db.Table('session_redcap', db.Model.metadata,
        db.Column('name', db.String(64), nullable=False),
        db.Column('num', db.Integer, nullable=False),
        db.Column('record_id', db.Integer, db.ForeignKey('redcap_records.id')),
        db.ForeignKeyConstraint(['name', 'num'],
                ['sessions.name', 'sessions.num']))

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
    dashboard_admin = db.Column('dashboard_admin', db.Boolean, default=False)
    is_active = db.Column('account_active', db.Boolean, default=False)

    studies = db.relationship('StudyUser', back_populates='user',
            order_by='StudyUser.study_id',
            collection_class=attribute_mapped_collection('study_id'))
    incidental_findings = db.relationship('IncidentalFinding')
    blacklist_comments = db.relationship('ScanBlacklist')
    timepoint_comments = db.relationship('TimepointComment')
    analysis_comments = db.relationship('AnalysisComment')
    sessions_reviewed = db.relationship('Session')

    def __init__(self, first, last, email=None, position=None, institution=None,
            phone1=None, phone2=None, github_name=None, gitlab_name=None,
            dashboard_admin=False, account_active=False):
        self.first_name = first
        self.last_name = last
        self.email = email
        self.position = position
        self.institution = institution
        self.phone1 = phone1
        self.phone2 = phone2
        self.github_name = github_name
        self.gitlab_name = gitlab_name
        self.dashboard_admin = dashboard_admin
        self.account_active = account_active

    def get_studies(self):
        """
        Get a list of Study objects that this user has access to.
        """
        if self.dashboard_admin:
            studies = Study.query.order_by(Study.id).all()
        else:
            studies = self.studies.keys()
        return studies

    def has_study_access(self, study):
        """
        Check if user has access to a specific study, or any study in a list.
        This function can take a string (representing a study ID), a Study
        object or a list of strings/Study objects.

        Note that if a list of studies is given only one must match a study the
        user has permission to access for 'true' to be returned.
        """
        if self.dashboard_admin:
            return True
        if isinstance(study, Study):
            study = study.id
        try:
            self.studies[study]
        except KeyError:
            return False
        return True

    def is_study_admin(self, study):
        if self.dashboard_admin:
            return True
        if isinstance(study, Study):
            study = study.id
        try:
            permissions = self.studies[study]
        except KeyError:
            return False
        return permissions.is_admin

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
    timepoints = db.relationship('Timepoint', secondary=study_timepoints_table,
            back_populates='studies', lazy='dynamic')
    scantypes = db.relationship('Scantype', secondary=study_scantype_table,
            back_populates='studies')

    def __init__(self, study_id, code=None, full_name=None, description=None):
        self.id = study_id
        self.code = code
        self.full_name = full_name
        self.description = description

    def num_timepoints(self, type=''):
        if type.lower() == 'human':
            timepoints = [timepoint for timepoint in self.timepoints
                    if not timepoint.is_phantom]
        elif type.lower() == 'phantom':
            timepoints = [timepoint for timepoint in self.timepoints
                    if timepoint.is_phantom]
        else:
            timepoints = self.timepoints
        return len(timepoints)

    def outstanding_issues(self):
        # use from_self to get a tuple of Session.name, Session.num like from
        # the other queries
        new_sessions = self.get_new_sessions().from_self(Session.name,
                Session.num).all()
        need_rewrite = self.needs_rewrite()
        missing_redcap = self.get_missing_redcap()
        missing_scans = self.get_missing_scans()

        new_label = '<td class="col-xs-2"><span class="fa-layers fa-fw" ' + \
                'style="font-size: 38px;"><i class="fas ' + \
                'fa-certificate" style="color: tomato"></i>' + \
                '<span class="fa-layers-text fa-inverse" ' + \
                'data-fa-transform="shrink-11.5 rotate--30" ' + \
                'style="font-weight:900">NEW</span></span></td>'
        rewrite_label = '<td class="col-xs-2"><span class="label ' + \
                'qc-warnings label-danger" title="Repeat session not on QC ' + \
                'page. Regenerate page by running dm_qc_report.py with the ' + \
                '--rewrite flag">Needs Rewrite</span></td>'
        scans_label = '<td class="col-xs-2"><span class="label qc-warnings ' + \
                'label-warning" title="Participant exists in REDCap but ' + \
                'does not have scans">Missing Scans</span></td>'
        redcap_label = '<td class="col-xs-2"><span class="label ' + \
                'qc-warnings label-info" title="Participant ' + \
                'does not have a REDCap survey even though this scan ' + \
                'site collects them">Missing REDCap</span></td>'

        issues = {}
        # Using default_row[:] in setdefault() to make sure each row has its
        # own copy of the default row
        default_row = ['<td></td>'] * 4
        for session in new_sessions:
            issues.setdefault(session, default_row[:])[0] = new_label
        for session in need_rewrite:
            issues.setdefault(session, default_row[:])[1] = rewrite_label
        for session in missing_scans:
            issues.setdefault(session, default_row[:])[2] = scans_label
        for session in missing_redcap:
            issues.setdefault(session, default_row[:])[3] = redcap_label

        return issues

    def get_new_sessions(self):
        # Doing this 'manually' to prevent SQLAlchemy from sending one query per
        # timepoint per study
        new = db.session.query(Session).filter(Session.signed_off == False) \
                .join(Timepoint).filter(Timepoint.is_phantom == False) \
                .join(study_timepoints_table,
                        and_(study_timepoints_table.c.timepoint == Timepoint.name,
                        study_timepoints_table.c.study == self.id))
        return new

    def get_sessions_using_redcap(self):
        """
        Returns a query that will find all sessions in the current study that
        expect a redcap survey (whether or not we've already received one for
        them)

        Doing this manually rather than letting SQLAlchemy handle it behind
        the scenes because it was firing off one query per session every time a
        study page loaded. So it's way uglier, but way faster. Sorry :(
        """
        uses_redcap = db.session.query(Session, session_redcap_table) \
                .outerjoin(session_redcap_table) \
                .join(Timepoint) \
                .join(study_timepoints_table,
                        and_(study_timepoints_table.c.timepoint == Timepoint.name,
                        study_timepoints_table.c.study == self.id)) \
                .join(StudySite,
                        and_(StudySite.site_id == Timepoint.site_id,
                        StudySite.study_id == study_timepoints_table.c.study)) \
                .filter(Timepoint.is_phantom == False) \
                .filter(StudySite.uses_redcap == True)

        return uses_redcap

    def get_missing_redcap(self):
        """
        Returns a list of all non-phantoms for the current study
        that are expecting a redcap survey but dont yet have one.
        """
        uses_redcap = self.get_sessions_using_redcap()
        sessions = uses_redcap.filter(session_redcap_table.c.name == None)\
                .from_self(Session.name, Session.num)
        return sessions.all()

    def get_missing_scans(self):
        """
        Returns a list of session names + repeat numbers for sessions in this
        study that have a scan completed survey but no scan data yet. Excludes
        session IDs that have explicitly been marked as never expecting data
        """
        uses_redcap = self.get_sessions_using_redcap()
        sessions = uses_redcap.filter(session_redcap_table.c.record_id != None)\
                .filter(~exists().where(and_(Scan.timepoint == Session.name,
                        Scan.repeat == Session.num))) \
                .filter(~exists().where(and_(Session.name == EmptySession.name,
                        Session.num == EmptySession.num))) \
                .from_self(Session.name, Session.num)
        return sessions.all()

    def needs_rewrite(self):
        """
        Return a list of (Session.name, Session.num) that aren't on their
        timepoint's QC page (i.e. sessions that require the timepoint static
        pages to be rewritten).
        """
        repeated = db.session.query(Session.name,
                        func.count(Session.name).label('num')) \
                .join(Timepoint) \
                .group_by(Session.name) \
                .having(func.count(Session.name) > 1).subquery()

        need_rewrite = db.session.query(Session) \
                .join(Timepoint) \
                .join(study_timepoints_table,
                        and_(study_timepoints_table.c.timepoint == Timepoint.name,
                        study_timepoints_table.c.study == self.id)) \
                .join(repeated) \
                .filter(Timepoint.last_qc_repeat_generated < repeated.c.num) \
                .filter(Session.num > Timepoint.last_qc_repeat_generated) \
                .from_self(Session.name, Session.num)

        return need_rewrite.all()

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

    def get_primary_contacts(self):
        contacts = [study_user.user for study_user in self.users
                if study_user.primary_contact]
        return contacts

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
    # This column should be removed when the static QC pages are made obsolete
    last_qc_repeat_generated =  db.Column('last_qc_generated', db.Integer,
            nullable=False, default=1)

    site = db.relationship('Site', uselist=False, back_populates='timepoints')
    studies = db.relationship('Study', secondary=study_timepoints_table,
            back_populates='timepoints',
            collection_class=attribute_mapped_collection('id'))
    sessions = db.relationship('Session', lazy='joined')
    comments = db.relationship('TimepointComment')
    incidental_findings = db.relationship('IncidentalFinding')

    def __init__(self, name, site, is_phantom=False, github_issue=None,
            gitlab_issue=None):
        self.name = name
        self.site = site
        self.is_phantom = is_phantom
        self.github_issue = github_issue
        self.gitlab_issue = gitlab_issue

    def belongs_to(self, study):
        """
        Returns true if the data in this Timepoint is considered part of the
        given study
        """
        if isinstance(study, Study):
            study = study.id
        try:
            self.studies[study]
        except KeyError:
            return False
        return True

    def is_qcd(self):
        if self.is_phantom:
            return True
        return all(sess.is_qcd() for sess in self.sessions)

    def __repr__(self):
        return "<Timepoint {}>".format(self.name)


class Session(db.Model):
    __tablename__ = 'sessions'

    name = db.Column('name', db.String(64), db.ForeignKey('timepoints.name'),
            primary_key=True)
    num = db.Column('num', db.Integer, primary_key=True)
    date = db.Column('date', db.DateTime)
    signed_off = db.Column('signed_off', db.Boolean, default=False)
    reviewer_id = db.Column('reviewer', db.Integer, db.ForeignKey('users.id'))
    review_date = db.Column('review_date', db.DateTime(timezone=True))


    redcap_record = db.relationship('RedcapRecord',
            secondary=session_redcap_table, back_populates='sessions',
            uselist=False)
    timepoint = db.relationship('Timepoint', uselist=False,
            back_populates='sessions')
    scans = db.relationship('Scan')
    reviewer = db.relationship('User', uselist=False,
            back_populates='sessions_reviewed')

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

    # def expecting_scans(self):
    #     return (self.redcap_record and not self.scans)

    def __repr__(self):
        return "<Session {}, {}>".format(self.name, self.num)

class EmptySession(db.Model):
    """
    This table exists solely so QCers can dismiss errors about empty sessions
    and comment on any follow up they've performed.
    """
    __tablename__ = 'empty_sessions'

    name = db.Column('name', db.String(64), primary_key=True, nullable=False)
    num = db.Column('num', db.Integer, primary_key=True, nullable=False)
    comment = db.Column('comment', db.Text, nullable=False)
    timestamp = db.Column('date_added', db.DateTime(timezone=True),
            nullable=False)
    user_id = db.Column('user', db.Integer, db.ForeignKey('users.id'),
            nullable=False)

    reviewer = db.relationship('User', uselist=False, lazy='joined')


    def __init__(self, name, num, comment=None):
        self.name = name
        self.num = num
        self.comment = comment

    def __repr__(self):
        return "<EmptySession {}, {}>".format(self.name, self.num)

    __table_args__ = (ForeignKeyConstraint(['name', 'num'],
            ['sessions.name', 'sessions.num']),)

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
    other_ids = db.relationship('Scan')
    session = db.relationship('Session', uselist=False, back_populates='scans')
    scantype = db.relationship('Scantype', uselist=False, back_populates='scans')
    analysis_comments = db.relationship('AnalysisComment')
    metric_values = db.relationship('MetricValue', cascade='all, delete-orphan')

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

    sessions = db.relationship('Session', secondary=session_redcap_table,
            back_populates='redcap_record')

    __table_args__ = (UniqueConstraint(record, project, url, event_id),)

    def __init__(self, record, project, url, event_id=None):
        self.record = record
        self.project = project
        self.url = url
        self.event_id = event_id

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
    __tablename__ = 'study_sites'

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
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column('date_reported', db.DateTime(timezone=True),
            nullable=False)

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
