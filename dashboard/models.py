"""
Object definition file for dashboard app
Each class defines a table in the database.

Of interest, check out sessions.validate_comment() and scan.validate_comment()
The @validates decorator ensures this is run before the checklist comment
    field can be updated in the database. This is what ensures the filesystem
    checklist.csv is in sync with the database.
"""

from dashboard import db
import utils
from hashlib import md5
from sqlalchemy.orm import validates
from sqlalchemy.schema import UniqueConstraint
from flask_login import UserMixin
import os
import logging
from flask import flash

logger = logging.getLogger(__name__)

"""
These following lines define many - many links between tables.
i.e. a study can have many sites and a site can be part of many studies.
This type of definition requires a _linking_ table in SQL.
"""
study_site_table = db.Table('study_site',
                            db.Column('study_id', db.Integer,
                                      db.ForeignKey('studies.id')),
                            db.Column('site_id', db.Integer,
                                      db.ForeignKey('sites.id')))

study_scantype_table = db.Table('study_scantypes',
                                db.Column('study_id', db.Integer,
                                          db.ForeignKey('studies.id')),
                                db.Column('scantype_id', db.Integer,
                                          db.ForeignKey('scantypes.id')))

study_people_table = db.Table('study_people',
                              db.Column('study_id', db.Integer,
                                        db.ForeignKey('studies.id')),
                              db.Column('person_id', db.Integer,
                                        db.ForeignKey('people.id')))
study_user_table = db.Table('study_users',
                            db.Column('study_id', db.Integer,
                                      db.ForeignKey('studies.id')),
                            db.Column('user_id', db.Integer,
                                      db.ForeignKey('users.id')))
# session_scan_table = db.Table('session_scans',
#                               db.Column('session_id', db.Integer,
#                                         db.ForeignKey('sessions.id')),
#                               db.Column('scan_id', db.Integer,
#                                         db.ForeignKey('scans.id')),
#                               db.Column('scan_name', db.String(128)),
#                               db.Column('is_primary', db.Boolean, default=False))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    realname = db.Column(db.String(64))
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    studies = db.relationship('Study', secondary=study_user_table,
                              back_populates='users')
    is_admin = db.Column(db.Boolean, default=False)
    has_phi = db.Column(db.Boolean, default=False)
    analysis_comments = db.relationship('ScanComment')
    incidental_findings = db.relationship('IncidentalFinding')

    def get_studies(self):
        # returns the list of studies that a user has access to
        if self.is_admin:
            studies = Study.query.order_by(Study.nickname).all()
        else:
            studies = self.studies
        return(studies)

    def has_study_access(self, study):
        if not isinstance(study, Study):
            # see is we can get by id
            study = Study.query.get(study)
            if not study:
                study = Study.query.filter_by(nickname=study)

        if self.is_admin or study in self.studies:
            return True
        else:
            return

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(username=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(username=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except:
            return str(self.id)  # python 3

    def avatar(self, size):
        if self.email:
            return 'http://www.gravatar.com/avatar/{}?d=mm&s={}'.format(
                md5(self.email.encode('utf-8')).hexdigest(),
                size)
        else:
            return 'http://www.gravatar.com/avatar/{}?d=mm&s={}'.format(
                md5('this isnt here').hexdigest(),
                size)


class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(12), index=True, unique=True)
    name = db.Column(db.String(64))
    scantypes = db.relationship('ScanType', secondary=study_scantype_table,
                                back_populates='studies')
    sites = db.relationship('Site', secondary=study_site_table,
                            back_populates='studies')
    sessions = db.relationship('Session')
    description = db.Column(db.String(1024))
    fullname = db.Column(db.String(1024))
    primary_contact_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    primary_contact = db.relationship('Person')
    users = db.relationship('User', secondary=study_user_table,
                            back_populates='studies')

    def __repr__(self):
        return ('<Study {}>'.format(self.nickname))

    def get_valid_metric_names(self):
        """return a list of metric names with duplicates removed"""
        valid_fmri_scantypes = ['IMI', 'RST', 'EMP', 'OBS', 'SPRL', 'VN-SPRL']
        names = []
        for scantype in self.scantypes:
            for metrictype in scantype.metrictypes:
                if scantype.name.startswith('DTI'):
                    names.append(('DTI', metrictype.name))
                elif scantype.name in valid_fmri_scantypes:
                    names.append(('FMRI', metrictype.name))
                elif scantype.name == 'T1':
                    names.append(('T1', metrictype.name))

        names = sorted(set(names))
        return(names)

    def session_count(self, type=None):
        if type.lower() == 'human':
            sessions = [session for session
                        in self.sessions
                        if not session.is_phantom]
        elif type.lower() == 'phantom':
            sessions = [session for session
                        in self.sessions
                        if session.is_phantom]
        else:
            sessions = [session for session
                        in self.sessions]

        return(len(sessions))


class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    studies = db.relationship('Study', secondary=study_site_table,
                              back_populates='sites')
    sessions = db.relationship('Session')

    def __repr__(self):
        return ('<Site {}>'.format(self.name))


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    date = db.Column(db.DateTime)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'),
                         nullable=False)
    study = db.relationship('Study', back_populates='sessions')
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    site = db.relationship('Site', back_populates='sessions')
    #scans = db.relationship('Scan', order_by="Scan.series_number",
    #                        cascade="all, delete-orphan")
    scans = db.relationship('Session_Scan',
                            back_populates='session')
    is_phantom = db.Column(db.Boolean)
    is_repeated = db.Column(db.Boolean)
    repeat_count = db.Column(db.Integer)
    last_repeat_qc_generated = db.Column(db.Integer, default=1)
    last_repeat_qcd = db.Column(db.Integer)
    cl_comment = db.Column(db.String(1024))
    gh_issue = db.Column(db.Integer)
    redcap_record = db.Column(db.Integer)  # ID of the record in redcap
    redcap_entry_date = db.Column(db.Date)  # date of record entry in redcap
    redcap_user = db.Column(db.Integer)  # ID of the user who filled in the redcap record
    redcap_comment = db.Column(db.String(3072))  # Redcap comment field
    redcap_url = db.Column(db.String(1024))  # URL for the redcap server
    redcap_projectid = db.Column(db.Integer)  # ID for redcap Project
    redcap_instrument = db.Column(db.String(1024))  # name of the redcap form
    incidental_findings = db.relationship('IncidentalFinding')

    def __repr__(self):
        return('<Session {} from Study {} at Site {}>'
               .format(self.name,
                       self.study.nickname,
                       self.site.name))

    def is_qcd(self):
        """checks if session has (ever) been quality checked"""
        if self.cl_comment:
            return True

    def is_current_qcd(self):
        """
        checks if the most recent repeat of a session has been quality checked
        """
        if self.last_repeat_qcd == self.repeat_count:
            return True

    def get_qc_doc(self):
        """Return the absolute path to the session qc doc if it exists"""
        return(utils.get_qc_doc(str(self.name)))

    def flush_changes(self):
        """Flush changes to the object back to the database"""
        db.session.add(self)
        db.session.commit()

    def scan_count(self):
        return len(self.scans)

    @property
    def incidental_finding(self):
        return len(self.incidental_findings)


    @validates('cl_comment')
    def validate_comment(self, key, comment):
        """
        check the comment isn't empty and that the checklist.csv can be updated
        """
        assert comment
        assert utils.update_checklist(self.name,
                                      comment,
                                      study_name=self.study.nickname)
        self.last_repeat_qcd = self.repeat_count
        return comment

    def delete(self):
        """
        Takes care of deleting a session.
        If session scans are linked to other projects, also deletes those records.
        """
        for scan_link in self.scans:
            if not scan_link.is_primary:
                # just delete the link record
                db.session.delete(scan_link)
            else:
                scan = scan_link.scan
                linked_scans = Session_Scan.query.filter(Session_Scan.scan_id == scan_link.scan_id)
                if linked_scans.count() > 1:
                    flash('Scan is linked in other studies')
                # first delete the scan, then the linking records
                for link in linked_scans:
                    db.session.delete(link)
                db.session.delete(scan)
        # finally delete the current session
        db.session.delete(self)
        db.session.commit()


class ScanType(db.Model):
    __tablename__ = 'scantypes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    metrictypes = db.relationship('MetricType', back_populates="scantype")
    scans = db.relationship("Scan", back_populates='scantype')
    studies = db.relationship("Study", secondary=study_scantype_table,
                              back_populates="scantypes")

    def __repr__(self):
        return('<ScanType {}>'.format(self.name))


class MetricType(db.Model):
    __tablename__ = 'metrictypes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12))
    scantype_id = db.Column(db.Integer, db.ForeignKey('scantypes.id'),
                            nullable=False)
    scantype = db.relationship('ScanType', back_populates='metrictypes')
    metricvalues = db.relationship('MetricValue')

    db.UniqueConstraint('name', 'scantype_id')

    def __repr__(self):
        return('<MetricType {}>'.format(self.name))


class Person(db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    role = db.Column(db.String(64))
    email = db.Column(db.String(255))
    phone1 = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))

    def __repr__(self):
        return('<Contact {}>'.format(self.name))


class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, unique=True)
    description = db.Column(db.String(128))
#   session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'),
#                          nullable=False)
#   session = db.relationship('Session', back_populates='scans')

    sessions = db.relationship('Session_Scan', back_populates='scan')
    scantype_id = db.Column(db.Integer, db.ForeignKey('scantypes.id'),
                            nullable=False)
    scantype = db.relationship('ScanType', back_populates="scans")
    metricvalues = db.relationship('MetricValue', cascade="all, delete-orphan")
    bl_comment = db.Column(db.String(1024))
    series_number = db.Column(db.Integer, nullable=False)
    repeat_number = db.Column(db.Integer)
    analysis_comments = db.relationship('ScanComment')

    def __repr__(self):
        return('<Scan {}>'.format(self.name))

    def is_blacklisted(self):
        if self.bl_comment:
            return True

    @property
    def comment_count(self):
        return len(self.analysis_comments)

    @validates('bl_comment')
    def validate_comment(self, key, comment):
        """
        check the comment isn't empty and that the blacklist.csv can be updated
        """
        assert comment, 'Comment not provided for scan:{}'.format(self.name)

        try:
            utils.update_blacklist('{}_{}'.format(self.name,
                                                  self.description),
                                   comment)
        except Exception as e:
            logger.error('Failed updating blacklist for scan: {}. '
                    'Reason: {}'.format(self.name, e.message))
            return False
        return comment

    def get_primary_session(self):
        """
        A scan object can have multiple sessions. On the file system
        this is represented with symlinks. The true data should only be
        stored in the study the scan was recorded under.
        """
        primary_session_link = Session_Scan.query.\
            filter(Session_Scan.scan_id == self.id,
                   Session_Scan.is_primary.is_(True))
        if primary_session_link.count() < 1:
            logger.error('Primary session not found for scan_id:{}. Check session_scan table.'
                         .format(self.id))
            return None
        return primary_session_link.first().session

    def get_file_path(self):
        session = self.get_primary_session()
        nii_path = utils.get_study_folder(study=session.study.nickname,
                                          folder_type='nii')

        # Hacky solution to account for the fact that we split PDT2s
        if self.scantype.name == 'PDT2':
            name = self.name.replace('_PDT2_', '_T2_')
        else:
            name = self.name

        file_name = '_'.join([name, self.description]) + '.nii.gz'
        path = os.path.join(nii_path, session.name, file_name)

        return path

    def get_hcp_path(self):
        """
        Returns the path to the scan hcp pipelines folder
        False if subject folder doesnt exists
        """
        session = self.get_primary_session()
        hcp_path = utils.get_study_folder(study=session.study.nickname,
                                          folder_type='hcp')
        sub_path = os.path.join(hcp_path,
                                'qc_MNIfsaverage32k',
                                session.name)
        if not os.path.isdir(sub_path):
            return False

        return sub_path


class MetricValue(db.Model):
    __tablename__ = 'scanmetrics'

    id = db.Column(db.Integer, primary_key=True)
    _value = db.Column('value', db.String)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    scan = db.relationship('Scan', back_populates="metricvalues")
    metrictype_id = db.Column(db.Integer, db.ForeignKey('metrictypes.id'))
    metrictype = db.relationship('MetricType', back_populates="metricvalues")

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
                                                       self.metrictype.name,
                                                       self.value))


class Analysis(db.Model):
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    software = db.Column(db.String)
    analysis_comments = db.relationship('ScanComment')

    def get_users(self):
        """
        Returns a list of unique user objects who have posted comments
        on this analysis.
        """
        user_ids = [comment.user_id for comment in self.analysis_comments]
        user_ids = set(user_ids)
        users = [User.query.get(uid) for uid in user_ids]
        return users

    def __repr__(self):
        return('<Analysis:{} {}>'.format(self.id, self.name))


class ScanComment(db.Model):
    __tablename__ = 'scan_comments'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    scan = db.relationship('Scan', back_populates="analysis_comments")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates="analysis_comments")
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'),
                            nullable=False)
    analysis = db.relationship('Analysis', back_populates="analysis_comments")
    excluded = db.Column(db.Boolean, default=False)
    comment = db.Column(db.String)


class IncidentalFinding(db.Model):
        __tablename__ = 'incidental_findings'

        id = db.Column(db.Integer, primary_key=True)
        session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'),
                               nullable=False)
        session = db.relationship('Session',
                                  back_populates="incidental_findings")
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            nullable=False)
        user = db.relationship('User', back_populates="incidental_findings")

class Session_Scan(db.Model):
    """
    This is a join table for the many-many relationship between scans and sessions.
    It's done this way so we can put extra information such as a different scan name
    and whether this relation shows the primary study for a scan.

    Access through the ORM is simple, Session.scans and Scan.sessions
    Access to the actual scan is a bit more complex
    for scanlink in session.scans:
        scanlink.scan.name

    Using a join statement is a bit more complex
    q = db.session.query(Scan)
    q = q.join(Session_Scans, Scan.sessions)
    q = q.join(Session, Session_Scans.session)
    """
    __tablename__ = 'session_scans'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'))
    scan_name = db.Column(db.String(128))
    is_primary = db.Column(db.Boolean, default=False)
    scan = db.relationship("Scan", back_populates="sessions")
    session = db.relationship("Session", back_populates="scans")
    # not a typo ",None" needed to enforce tuple structure
    __table_args__ = (UniqueConstraint(session_id, scan_id, name="session_scan"),None)
