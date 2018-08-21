"""
Object definition file for dashboard app
Each class defines a table in the database.

Of interest, check out sessions.validate_comment() and scan.validate_comment()
The @validates decorator ensures this is run before the checklist comment
    field can be updated in the database. This is what ensures the filesystem
    checklist.csv is in sync with the database.
"""
import logging

from dashboard import db
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint


logger = logging.getLogger(__name__)

################################################################################
# Plain entities

class User(db.Model):
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
    account_active = db.Column('account_active', db.Boolean, default=False)

    studies = db.relationship('StudyUser', back_populates='user')

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

    def __repr__(self):
        return "<User {}: {} {}>".format(self.id, self.first_name,
                self.last_name)

class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column('id', db.String(32), primary_key=True)
    code = db.Column('study_code', db.String(32))
    full_name = db.Column('name', db.String(1024))
    description = db.Column('description', db.Text)

    users = db.relationship('StudyUser', back_populates='study')

    def __init__(self, study_id, code=None, full_name=None, description=None):
        self.id = study_id
        self.code = code
        self.full_name = full_name
        self.description = description

    def __repr__(self):
        return "<Study {}>".format(self.id)


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


class Site(db.Model):
    __tablename__ = 'sites'

    name = db.Column('name', db.String(64), primary_key=True)
    description = db.Column('description', db.Text)

    def __init__(self, site_name, description=None):
        self.name = site_name
        self.description = description

    def __repr__(self):
        return "<Site {}>".format(self.name)


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

    __table_args__ = (UniqueConstraint(record, project, url),)

    def __init__(self, record, project, url):
        self.record = record
        self.project = project
        self.url = url

    def __repr__(self):
        return "<RedcapRecord {}: record {} project {} url {}>".format(self.id,
                self.record, self.project, self.url)


# class Analysis(db.Model):
#     __tablename__ = 'analyses'
#
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(60), nullable=False)
#     description = db.Column(db.String(4096), nullable=False)
#     software = db.Column(db.String(4096))
#
#     analysis_comments = db.relationship('ScanComment')
#
#     def get_users(self):
#         """
#         Returns a list of unique user objects who have posted comments
#         on this analysis.
#         """
#         user_ids = [comment.user_id for comment in self.analysis_comments]
#         user_ids = set(user_ids)
#         users = [User.query.get(uid) for uid in user_ids]
#         return users
#
#     def __repr__(self):
#         return('<Analysis {}: {}>'.format(self.id, self.name))


################################################################################
# Linking tables (i.e. basic many to many relationships)

study_scantype_table = db.Table('study_scantypes',
        db.Column('study', db.Integer, db.ForeignKey('studies.id')),
        db.Column('scantype', db.Integer, db.ForeignKey('scantypes.tag')))

################################################################################
# Association Objects (i.e. many to many relationships with their own
# attributes/columns for each relationship).

class StudyUser(db.Model):
    __tablename__ = 'study_users'

    study_id = db.Column('study_id', db.String(32), db.ForeignKey('studies.id'),
            nullable=False, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False, primary_key=True)
    phi_access = db.Column('phi_access', db.Boolean, default=False)
    is_admin = db.Column('is_admin', db.Boolean, default=False)
    primary_contact = db.Column('primary_contact', db.Boolean, default=False)
    staff_contact = db.Column('staff_contact', db.Boolean, default=False)
    does_qc = db.Column('does_qc', db.Boolean, default=False)

    study = db.relationship('Study', back_populates='users')
    user = db.relationship('User', back_populates='studies')

    def __init__(self, study_id, user_id, phi=False, admin=False,
            is_primary_contact=False, is_staff_contact=False, does_qc=False):
        self.study_id = study_id
        self.user_id = user_id
        self.phi_access = phi
        self.is_admin = admin
        self.primary_contact = is_primary_contact
        self.staff_contact = is_staff_contact
        self.does_qc = does_qc

    def __repr__(self):
        return "<StudyUser Study: {} User: {}>".format(self.study_id,
                self.user_id)

# class ScanComment(db.Model):
#     __tablename__ = 'scan_comments'
#
#     id = db.Column(db.Integer, primary_key=True)
#     # scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
#     # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'),
#             nullable=False)
#     excluded = db.Column(db.Boolean, default=False)
#     comment = db.Column(db.String(4096))
#
#     scan = db.relationship('Scan', back_populates="analysis_comments")
#     analysis = db.relationship('Analysis', back_populates="analysis_comments")
#     user = db.relationship('User', back_populates="analysis_comments")
#
#     def __repr__(self):
#         return "<ScanComment {}: Analysis {} comment on scan {} by user {}>".format(
#                 self.id, self.analysis_id, self.scan_id, self.user_id)

# class IncidentalFinding(db.Model):
#     __tablename__ = 'incidental_findings'
#
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
#             nullable=False)
#     session_id = db.Column(db.String(64), db.ForeignKey('sessions.id'),
#             nullable=False)
#
#     session = db.relationship('Session',
#             back_populates="incidental_findings")
#     user = db.relationship('User', back_populates="incidental_findings")
#
#     def __repr__(self):
#         return "<IncidentalFinding {} for Session {} found by User {}>".format(
#                 self.id, self.session_id, self.user_id)
