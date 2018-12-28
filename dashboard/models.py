"""
Object definition file for dashboard app
Each class defines a table in the database.

Of interest, check out sessions.validate_comment() and scan.validate_comment()
The @validates decorator ensures this is run before the checklist comment
    field can be updated in the database. This is what ensures the filesystem
    checklist.csv is in sync with the database.
"""
import os
import datetime
import logging
from random import randint

from flask_login import UserMixin
from sqlalchemy import and_, exists, func
from sqlalchemy.orm import deferred
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.exc import IntegrityError
from psycopg2.tz import FixedOffsetTimezone

from dashboard import db, TZ_OFFSET
from dashboard.utils import get_study_path
from dashboard.emails import account_request_email, account_activation_email, \
        account_rejection_email
from datman import scanid

logger = logging.getLogger(__name__)

class InvalidDataException(Exception):
    """
    Default exception when user tries to insert something obviously wrong.
    """

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
    phone = db.Column('phone', db.String(20))
    ext = db.Column('ext', db.String(10))
    alt_phone = db.Column('alt_phone', db.String(20))
    alt_ext = db.Column('alt_ext', db.String(10))
    _username = db.Column('username', db.String(70))
    picture = db.Column('picture', db.String(2048))
    dashboard_admin = db.Column('dashboard_admin', db.Boolean, default=False)
    is_active = db.Column('account_active', db.Boolean, default=False)

    studies = db.relationship('StudyUser', back_populates='user',
            order_by='StudyUser.study_id',
            collection_class=attribute_mapped_collection('study_id'))
    incidental_findings = db.relationship('IncidentalFinding')
    scan_comments = db.relationship('ScanChecklist')
    timepoint_comments = db.relationship('TimepointComment')
    analysis_comments = db.relationship('AnalysisComment')
    sessions_reviewed = db.relationship('Session')
    pending_approval = db.relationship('AccountRequest', uselist=False,
            cascade="all, delete")

    def __init__(self, first, last, username=None, provider='github',email=None,
            position=None, institution=None, phone=None, ext=None,
            alt_phone=None, alt_ext=None, picture=None,
            dashboard_admin=False, account_active=False):
        self.first_name = first
        self.last_name = last
        self.email = email
        self.position = position
        self.institution = institution
        self.phone = phone
        self.ext = ext
        self.alt_phone = alt_phone
        self.alt_ext = alt_ext
        if username:
            self.update_username(username, provider)
        self.picture = picture
        self.dashboard_admin = dashboard_admin
        self.account_active = account_active

    def update_username(self, new_name, provider='github'):
        # Make sure the username is globally unique by adding a prefix based on
        # the oauth provider
        if provider == 'github':
            self._username = "gh_" + new_name
        else:
            # gitlab is the only alt provider for now
            self._username = "gl_" + new_name

    @property
    def username(self):
        try:
            uname = self._username.split("_")[1]
        except AttributeError:
            uname = ""
        return uname

    @property
    def account_provider(self):
        if not self._username:
            return None
        if self._username.startswith('gl_'):
            return 'gitlab'
        return 'github'

    def update_avatar(self, url=None):
        if url is None or url == self.picture:
            return
        self.picture = url
        self.save_changes()

    def request_account(self, request_form):
        request_form.populate_obj(self)
        # This is needed because the form sets it to an empty string, which
        # causes postgres to throw an error (it expects an int)
        self.id = None
        try:
            self.save_changes()
            request = AccountRequest(self.id)
            db.session.add(request)
            db.session.commit()
        except IntegrityError:
            # Account exists or request is already pending
            db.session.rollback()
        else:
            account_request_email(self.first_name, self.last_name)

    def num_requests(self):
        """
        Returns a count of all pending user requests that need to be reviewed
        """
        if not self.dashboard_admin:
            return 0
        return AccountRequest.query.count()

    def add_studies(self, study_ids):
        for study in study_ids:
            record = StudyUser(study, self.id)
            self.studies[study] = record
        self.save_changes()

    def remove_studies(self, study_ids):
        if not isinstance(study_ids, list):
            study_ids = [study_ids]
        for study in study_ids:
            if isinstance(study, StudyUser):
                study = study.study_id
            db.session.delete(self.studies[study])
        self.save_changes()

    def get_studies(self):
        """
        Get a list of Study objects that this user has access to.
        """
        if self.dashboard_admin:
            studies = Study.query.order_by(Study.id).all()
        else:
            studies = [su.study for su in self.studies.values()]
        return studies

    def get_disabled_studies(self):
        """
        Get a list of Study objects the user does NOT have access to.
        """
        enabled_studies = self.studies.keys()

        if enabled_studies:
            disabled_studies = Study.query.filter(
                    ~Study.id.in_(enabled_studies)).all()
        else:
            disabled_studies = Study.query.all()

        return disabled_studies

    def has_study_access(self, study):
        return self._get_permissions(study)

    def is_study_admin(self, study):
        return self._get_permissions(study, perm='is_admin')

    def is_primary_contact(self, study):
        return self._get_permissions(study, perm='primary_contact')

    def is_kimel_contact(self, study):
        return self._get_permissions(study, perm='kimel_contact')

    def is_study_RA(self, study):
        return self._get_permissions(study, perm='study_RA')

    def does_qc(self, study):
        return self._get_permissions(study, perm='does_qc')

    def _get_permissions(self, study, perm=None):
        """
        Checks the StudyUser records for this user. If no key is given it
        checks if a record exists for a specific study (i.e. if the user has
        access to that study). If 'perm' is set it can check a specific
        permission attribute (e.g. 'is_admin' or 'has_phi').

        Always returns a boolean.
        """
        if self.dashboard_admin:
            return True
        if isinstance(study, Study):
            study = study.id
        try:
            permissions = self.studies[study]
        except KeyError:
            return False
        if perm:
            return getattr(permissions, perm)
        return True

    def save_changes(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<User {}: {} {}>".format(self.id, self.first_name,
                self.last_name)

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)

class AccountRequest(db.Model):
    __tablename__ = 'account_requests'

    user_id = db.Column('user_id', db.Integer, db.ForeignKey("users.id"),
            primary_key=True)

    user = db.relationship('User', uselist=False)

    def __init__(self, user_id):
        self.user_id = user_id

    def approve(self):
        try:
            self.user.is_active = True
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Account activation failed for user {}. Reason: "
                    "{}".format(self.user_id, e))
            raise e
        else:
            account_activation_email(self.user)

    def reject(self):
        try:
            db.session.delete(self.user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Account request rejection failed for user {}. "
                    "Reason: {}".format(self.user_id, e))
            raise e
        else:
            account_rejection_email(self.user)

    def __repr__(self):
        return "<User {} Requires Admin Review>".format(self.user_id)

    def __str__(self):
        if self.user:
            result = "{} {} requests access under username {}".format(
                    self.user.first_name, self.user.last_name,
                    self.user.username)
        else:
            result = "User with ID {} requests dashboard access".format(
                    self.user_id)
        return result

class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column('id', db.String(32), primary_key=True)
    name = db.Column('name', db.String(1024))
    description = db.Column('description', db.Text)
    read_me = deferred(db.Column('read_me', db.Text))

    users = db.relationship('StudyUser', back_populates='study')
    sites = db.relationship('StudySite', back_populates='study',
            collection_class=attribute_mapped_collection('site_id'))
    timepoints = db.relationship('Timepoint', secondary=study_timepoints_table,
            back_populates='studies', lazy='dynamic')
    scantypes = db.relationship('Scantype', secondary=study_scantype_table,
            back_populates='studies')

    def __init__(self, study_id, full_name=None, description=None, read_me=None):
        self.id = study_id
        self.full_name = full_name
        self.description = description
        self.read_me = read_me

    def add_timepoint(self, timepoint):
        if isinstance(timepoint, scanid.Identifier):
            timepoint = Timepoint(timepoint.get_full_subjectid_with_timepoint(),
                    timepoint.site, is_phantom=scanid.is_phantom(timepoint))

        if not isinstance(timepoint, Timepoint):
            raise InvalidDataException("Invalid input to 'add_timepoint()': "
                    "instance of dashboard.models.Timepoint or "
                    "datman.scanid.Identifier expected")

        if timepoint.site_id not in self.sites.keys():
            raise InvalidDataException("Timepoint's site {} is not configured "
                    "for study {}".format(timepoint.site_id, self.id))
        self.timepoints.append(timepoint)
        try:
            db.session.add(self)
            db.session.commit()
        except FlushError as e:
            db.session.rollback()
            raise InvalidDataException("Can't add timepoint {}. Already "
                    "exists.".format(timepoint))
        except Exception as e:
            db.session.rollback()
            e.message = "Failed to add timepoint {}. Reason: {}".format(
                    timepoint, e)
            raise
        return timepoint

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
                'style="font-size: 28px;"><i class="fas ' + \
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
            issues.setdefault(session[0], default_row[:])[0] = new_label
        for session in need_rewrite:
            issues.setdefault(session[0], default_row[:])[1] = rewrite_label
        for session in missing_scans:
            issues.setdefault(session[0], default_row[:])[2] = scans_label
        for session in missing_redcap:
            issues.setdefault(session[0], default_row[:])[3] = redcap_label

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
        uses_redcap = db.session.query(Session, SessionRedcap) \
                .outerjoin(SessionRedcap) \
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
        sessions = uses_redcap.filter(SessionRedcap.name == None)\
                .from_self(Session.name, Session.num)
        return sessions.all()

    def get_missing_scans(self):
        """
        Returns a list of session names + repeat numbers for sessions in this
        study that have a scan completed survey but no scan data yet. Excludes
        session IDs that have explicitly been marked as never expecting data
        """
        uses_redcap = self.get_sessions_using_redcap()
        sessions = uses_redcap.filter(SessionRedcap.record_id != None)\
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
                .filter(Timepoint.static_page != None) \
                .filter(Timepoint.last_qc_repeat_generated < repeated.c.num) \
                .filter(Session.num > Timepoint.last_qc_repeat_generated) \
                .from_self(Session.name, Session.num)

        return need_rewrite.all()

    def get_blacklisted_scans(self):
        query = self._get_checklist()
        blacklisted_scans =  query.filter(and_(ScanChecklist.approved == False,
                ScanChecklist.comment is not None))
        return blacklisted_scans.all()

    def get_flagged_scans(self):
        query = self._get_checklist()
        flagged_scans = query.filter(and_(ScanChecklist.approved == True,
                ScanChecklist.comment != None))
        return flagged_scans.all()

    def get_qced_scans(self):
        query = self._get_checklist()
        reviewed_scans = query.filter(and_(ScanChecklist.approved == True,
                ScanChecklist.comment == None))
        return reviewed_scans.all()

    def _get_checklist(self):
        query = db.session.query(ScanChecklist) \
            .join(Scan) \
            .join(study_timepoints_table,
                    and_(study_timepoints_table.c.timepoint == Scan.timepoint,
                    study_timepoints_table.c.study == self.id))
        return query

    def get_valid_metric_names(self):
        """
        Return a list of metric names with duplicates removed.

        TODO: This entire method needs to be updated to be less hard-coded. We
        should get the 'type' of scan from our config file 'qc_type' field
        instead (and store it in the database). For now I just got it
        working with the new schema - Dawn
        """
        valid_fmri_scantypes = ['IMI', 'RST', 'EMP', 'OBS', 'SPRL-COMB', 'VN-SPRL-COMB']
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

    def choose_staff_contact(self):
        kimel_contacts = [su.user for su in self.users if su.kimel_contact]
        if len(kimel_contacts) >= 1:
            user = self.select_next(kimel_contacts)
        else:
            user = None
        return user

    def select_next(self, user_list):
        """
        Selects the next user from a study. This can be used to choose
        the next QC-er to assign, or the next staff member to assign to an
        issue, etc.

        Current strategy is to pick a random person. This may be changed in
        the future.
        """
        next_idx = randint(0, len(user_list) - 1)
        return user_list[next_idx]

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Study {}>".format(self.id)


class Site(db.Model):
    __tablename__ = 'sites'

    name = db.Column('name', db.String(32), primary_key=True)
    description = db.Column('description', db.Text)

    studies = db.relationship('StudySite', back_populates='site',
            collection_class=attribute_mapped_collection('study.id'))
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
    # These columns should be removed when the static QC pages are made obsolete
    last_qc_repeat_generated =  db.Column('last_qc_generated', db.Integer,
            nullable=False, default=1)
    static_page = db.Column('static_page', db.String(1028))

    site = db.relationship('Site', uselist=False, back_populates='timepoints')
    studies = db.relationship('Study', secondary=study_timepoints_table,
            back_populates='timepoints',
            collection_class=attribute_mapped_collection('id'))
    sessions = db.relationship('Session', lazy='joined',
            collection_class=attribute_mapped_collection('num'),
            cascade='all, delete')
    comments = db.relationship('TimepointComment', cascade='all, delete',
            order_by='TimepointComment._timestamp')
    incidental_findings = db.relationship('IncidentalFinding',
            cascade='all, delete')

    def __init__(self, name, site, is_phantom=False, static_page=None):
        self.name = name
        self.site_id = site
        self.is_phantom = is_phantom
        self.static_page = static_page

    def add_session(self, num, date=None):
        session = Session(self.name, num, date=date)
        self.sessions[num] = session
        try:
            db.session.add(self)
            db.session.commit()
        except AssertionError as e:
            db.session.rollback()
            raise InvalidDataException("Session {} of timepoint {} already "
                    "exists".format(num, self.name))
        except Exception as e:
            db.session.rollback()
            e.message = "Failed to add session {} to timepoint {}. Reason: " \
                    "{}".format(num, self.name, e)
            raise
        return session

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

    def accessible_study(self, user):
        """
        Returns a study that the timepoint belongs to and the user has access to
        if one exists.
        """
        for study_name in self.studies:
            if user.has_study_access(study_name):
                return self.studies[study_name]
        return None

    def is_qcd(self):
        if self.is_phantom:
            return True
        return all(sess.is_qcd() for sess in self.sessions.values())

    def expects_redcap(self, study):
        return self.site.studies[study].uses_redcap

    def needs_redcap_survey(self, study_id):
        if self.is_phantom:
            return False
        uses_redcap = self.expects_redcap(study_id)
        return uses_redcap and any(not sess.redcap_record
                for sess in self.sessions.values())

    def needs_rewrite(self):
        if self.static_page and (self.last_qc_repeat_generated < len(self.sessions)):
            return True
        return False

    def missing_scans(self):
        if self.is_phantom:
            return False
        return any(sess.missing_scans() for sess in self.sessions.values())

    def dismiss_redcap_error(self, session_num):
        session_redcap = SessionRedcap(self.name, session_num)
        db.session.add(session_redcap)
        db.session.commit()

    def ignore_missing_scans(self, session_num, user_id, comment):
        empty_session = EmptySession(self.name, session_num, user_id, comment)
        db.session.add(empty_session)
        db.session.commit()

    def delete(self):
        """
        This will cascade and also delete any records that reference
        the current timepoint, so be careful :)
        """
        db.session.delete(self)
        db.session.commit()

    def report_incidental_finding(self, user_id, comment):
        new_finding = IncidentalFinding(user_id, self.name, comment)
        db.session.add(new_finding)
        db.session.commit()

    def update_comment(self, user_id, comment_id, new_text):
        comment = self.get_comment(comment_id)
        if user_id != comment.user_id:
            raise Exception('User does not have permission to modify comment')
        comment.update(new_text)

    def add_comment(self, user_id, text):
        new_comment = TimepointComment(self.name, user_id, text)
        db.session.add(new_comment)
        db.session.commit()

    def delete_comment(self, comment_id):
        comment = self.get_comment(comment_id)
        db.session.delete(comment)
        db.session.commit()

    def get_comment(self, comment_id):
        match = [comment for comment in self.comments
                if comment.id == comment_id]
        if not match:
            raise Exception('Comment not found.')
        return match[0]

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def __repr__(self):
        return "<Timepoint {}>".format(self.name)

    def __str__(self):
        return self.name


class TimepointComment(db.Model):
    __tablename__ = 'timepoint_comments'

    id = db.Column('id', db.Integer, primary_key=True)
    timepoint_id = db.Column('timepoint', db.String(64),
            db.ForeignKey('timepoints.name'), nullable=False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    _timestamp = db.Column('comment_timestamp', db.DateTime(timezone=True),
            nullable=False)
    comment = db.Column('comment', db.Text, nullable=False)
    modified = db.Column('modified', db.Boolean, default=False)

    user = db.relationship('User', uselist=False,
            back_populates='timepoint_comments')
    timepoint = db.relationship('Timepoint', uselist=False,
            back_populates='comments')

    def __init__(self, timepoint_id, user_id, comment):
        self.timepoint_id = timepoint_id
        self.user_id = user_id
        self.comment = comment
        self._timestamp = datetime.datetime.now(FixedOffsetTimezone(offset=TZ_OFFSET))

    def update(self, new_text):
        self.comment = new_text
        self.modified = True
        db.session.add(self)
        db.session.commit()

    @property
    def timestamp(self):
        return self._timestamp.strftime('%I:%M %p, %Y-%m-%d')

    def __repr__(self):
        return "<TimepointComment for {} by user {}>".format(self.timepoint_id,
                self.user_id)

class Session(db.Model):
    __tablename__ = 'sessions'

    name = db.Column('name', db.String(64), db.ForeignKey('timepoints.name'),
            primary_key=True)
    num = db.Column('num', db.Integer, primary_key=True)
    date = db.Column('date', db.DateTime)
    signed_off = db.Column('signed_off', db.Boolean, default=False)
    reviewer_id = db.Column('reviewer', db.Integer, db.ForeignKey('users.id'))
    review_date = db.Column('review_date', db.DateTime(timezone=True))

    reviewer = db.relationship('User', uselist=False,
            back_populates='sessions_reviewed')
    timepoint = db.relationship('Timepoint', uselist=False,
            back_populates='sessions')
    scans = db.relationship('Scan', cascade='all, delete')
    empty_session = db.relationship('EmptySession', uselist=False,
            back_populates='session', cascade='all, delete')
    redcap_record = db.relationship('SessionRedcap', back_populates='session',
            uselist=False, cascade='all, delete')

    def __init__(self, name, num, date=None, signed_off=False, reviewer_id=None, 
            review_date=None):
        self.name = name
        self.num = num
        self.date = date
        self.signed_off = signed_off
        self.reviewer_id = reviewer_id
        self.review_date = review_date

    def add_scan(self, name, series, tag, description=None, source_id=None):
        scan = Scan(name, self.name, self.num, series, tag, description,
                source_id)
        self.scans.append(scan)
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise InvalidDataException("Failed to add scan {}. Reason: "
                    "{}".format(name, e))
        return scan

    def delete_scan(self, name):
        match = [scan for scan in self.scans if scan.name == name]
        if not match:
            return
        try:
            db.session.delete(match[0])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            e.message = "Could not delete scan {}. Reason: {}".format(name,
                    e.message)
            raise e

    def add_redcap(self, record_num, project, url, instrument=None, date=None,
            rc_user=None, comment=None, version=None, event_id=None):
        if self.redcap_record:
            rc_record = self.redcap_record.record
            if (rc_record.record != record_num or
                    str(rc_record.project) != project or
                    rc_record.url != url):
                raise InvalidDataException("Existing record already found. "
                    "Please remove the old record before adding a new one.")
        else:
            rc_record = RedcapRecord(record_num, project, url)
            db.session.add(rc_record)
            # Flush to get an ID assigned
            db.session.flush()
            self.redcap_record = SessionRedcap(self.name, self.num, rc_record.id)
            self.save()

        if instrument:
            rc_record.instrument = instrument
        if date:
            rc_record.date = date
        if rc_user:
            rc_record.user = rc_user
        if comment:
            rc_record.comment = comment
        if version:
            rc_record.version = version
        db.session.add(rc_record)
        db.session.commit()
        return rc_record

    def is_qcd(self):
        if self.timepoint.is_phantom:
            return True
        return self.signed_off

    def missing_scans(self):
        if self.redcap_record and not self.scans and not self.empty_session:
            return True
        return False

    def sign_off(self, user_id):
        self.signed_off = True
        self.reviewer_id = user_id
        self.review_date = datetime.datetime.now(FixedOffsetTimezone(offset=TZ_OFFSET))
        db.session.add(self)
        db.session.commit()

    def is_new(self):
        return ((self.scans is None and self.missing_scans())
                or any([scan.is_new() for scan in self.scans]))

    def delete(self):
        """
        This will also delete anything referencing the current session (i.e.
        any scans, redcap comments, blacklist entries or dismissed 'missing
        scans' errors)
        """
        db.session.delete(self)
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Session {}, {}>".format(self.name, self.num)

    def __str__(self):
        return "{}_{:02}".format(self.name, self.num)

class EmptySession(db.Model):
    """
    This table exists solely so QCers can dismiss errors about empty sessions
    and comment on any follow up they've performed.
    """
    __tablename__ = 'empty_sessions'

    name = db.Column('name', db.String(64), primary_key=True, nullable=False)
    num = db.Column('num', db.Integer, primary_key=True, nullable=False)
    comment = db.Column('comment', db.String(2048), nullable=False)
    user_id = db.Column('reviewer', db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    date_added = db.Column('date_added', db.DateTime(timezone=True))

    session = db.relationship('Session', uselist=False,
            back_populates='empty_session')
    reviewer = db.relationship('User', uselist=False, lazy='joined')

    __table_args__ = (ForeignKeyConstraint(['name', 'num'],
            ['sessions.name', 'sessions.num']),)

    def __init__(self, name, num, user_id, comment):
        self.name = name
        self.num = num
        self.user_id = user_id
        self.comment = comment
        self.date_added = datetime.datetime.now(FixedOffsetTimezone(offset=TZ_OFFSET))

    def __repr__(self):
        return "<EmptySession {}, {}>".format(self.name, self.num)


class SessionRedcap(db.Model):
    # Using a class instead of an association table here to let us know when an
    # entry has been added without a redcap record (i.e. when a user has let us know
    # that a session is never going to get a redcap record)
    __tablename__ = 'session_redcap'

    name = db.Column('name', db.String(64), primary_key=True, nullable=False)
    num = db.Column('num', db.Integer, primary_key=True, nullable=False)
    record_id = db.Column('record_id', db.Integer,
            db.ForeignKey('redcap_records.id'))

    session = db.relationship('Session', back_populates='redcap_record',
            uselist=False)
    record = db.relationship('RedcapRecord', back_populates='sessions',
            uselist=False)

    __table_args__ = (ForeignKeyConstraint(['name', 'num'],
            ['sessions.name', 'sessions.num']),)

    def __init__(self, name, num, record_id=None):
        self.name = name
        self.num = num
        self.record_id = record_id

    def __repr__(self):
        return "<SessionRedcap {}, {} - record {}>".format(self.name,
                self.num, self.record_id)

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
    # If a scan is a link, this will hold the id of the source scan
    source_id = db.Column('source_data', db.Integer, db.ForeignKey(id))

    # If a scan has any symbolic links pointing to it 'links' will be a list
    # of them. If a scan is just a link pointing to some other data 'source_data'
    # will point to this original data.
    links = db.relationship('Scan', cascade='all, delete',
        backref=db.backref('source_data', remote_side=[id]))
    qc_review = db.relationship('ScanChecklist', uselist=False,
            back_populates='scan', cascade='all, delete', lazy='joined')
    session = db.relationship('Session', uselist=False, back_populates='scans')
    scantype = db.relationship('Scantype', uselist=False, back_populates='scans')
    analysis_comments = db.relationship('AnalysisComment', cascade='all, delete')
    metric_values = db.relationship('MetricValue', cascade='all, delete-orphan')

    __table_args__ = (ForeignKeyConstraint(['timepoint', 'session'],
            ['sessions.name', 'sessions.num']),
            UniqueConstraint(name))

    def __init__(self, name, timepoint, repeat, series, tag, description=None,
            source_id=None):
        self.name = name
        self.timepoint = timepoint
        self.repeat = repeat
        self.series = series
        self.tag = tag
        self.description = description
        self.source_id = source_id

    def get_path(self, study=None):
        if not study:
            study = self.session.timepoint.studies.values()[0].id
        nii_folder = get_study_path(study, folder='nii')
        fname = "_".join([self.name, self.description + ".nii.gz"])
        full_path = os.path.join(nii_folder, self.timepoint, fname)
        if not os.path.exists(full_path):
            full_path = full_path.replace(".nii.gz", ".nii")
        return os.path.realpath(full_path)

    @property
    def nifti_name(self):
        # This is needed for the papaya viewer - it requires the file name with
        # extension. If the real file is .gz and the given file name doesnt end
        # that way (or vice versa) the viewer crashes, so you need to actually
        # locate it on the file system, no short cuts :(
        return os.path.basename(self.get_path())

    def get_checklist_entry(self):
        if self.is_linked():
            checklist = self.source_data.qc_review
        else:
            checklist = self.qc_review
        return checklist

    def _new_checklist_entry(self, signing_user):
        if self.is_linked():
            return ScanChecklist(self.source_id, signing_user)
        return ScanChecklist(self.id, signing_user)

    def add_checklist_entry(self, signing_user, comment=None, sign_off=None):
        checklist = self.get_checklist_entry()
        if not checklist:
            checklist = self._new_checklist_entry(signing_user)
        checklist.update_entry(signing_user, comment, sign_off)
        checklist.save()

    def is_linked(self):
        return self.source_id is not None

    def is_new(self):
        checklist = self.get_checklist_entry()
        return checklist is None or (not checklist.comment and not checklist.approved)

    def signed_off(self):
        checklist = self.get_checklist_entry()
        return checklist.approved and not checklist.comment

    def flagged(self):
        checklist = self.get_checklist_entry()
        return checklist.approved and checklist.comment is not None

    def blacklisted(self):
        checklist = self.get_checklist_entry()
        return checklist.comment is not None and not checklist.approved

    def get_comment(self):
        checklist = self.get_checklist_entry()
        return checklist.comment or ""

    def list_children(self):
        return [link.name for link in self.links]

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        if self.source_id:
            repr = "<Scan {}: {} link to scan {}>".format(self.id, self.name,
                    self.source_id)
        else:
            repr = "<Scan {}: {}>".format(self.id, self.name)
        return repr

    def __str__(self):
        return self.name


class ScanChecklist(db.Model):
    __tablename__ = 'scan_checklist'

    id = db.Column('id', db.Integer, primary_key=True)
    scan_id = db.Column('scan_id', db.Integer, db.ForeignKey('scans.id'),
            nullable=False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
            nullable=False)
    _timestamp = db.Column('review_timestamp', db.DateTime(timezone=True))
    comment = db.Column('comment', db.String(1028))
    approved = db.Column('signed_off', db.Boolean, nullable=False, default=False)

    scan = db.relationship('Scan', uselist=False, back_populates='qc_review')
    user = db.relationship('User', uselist=False,
            back_populates='scan_comments')


    __table_args__ = (UniqueConstraint(scan_id),)

    def __init__(self, scan_id, user_id, comment=None, approved=False):
        self.scan_id = scan_id
        self.user_id = user_id
        self.comment = comment
        self.approved = approved

    @property
    def timestamp(self):
        return self._timestamp.strftime('%I:%M %p, %Y-%m-%d')

    def update_entry(self, user_id, comment=None, status=None):
        if status is not None:
            self.approved = status
        if comment is not None:
            self.comment = comment
        self.user_id = user_id
        self._timestamp = datetime.datetime.now(FixedOffsetTimezone(offset=TZ_OFFSET))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<ScanChecklist for {} by user {}>".format(self.scan_id,
                self.user_id)

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

    sessions = db.relationship('SessionRedcap', back_populates='record')

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
    is_admin = db.Column('is_admin', db.Boolean, default=False)
    primary_contact = db.Column('primary_contact', db.Boolean, default=False)
    kimel_contact = db.Column('kimel_contact', db.Boolean, default=False)
    study_RA = db.Column('study_ra', db.Boolean, default=False)
    does_qc = db.Column('does_qc', db.Boolean, default=False)

    study = db.relationship('Study', back_populates='users')
    user = db.relationship('User', back_populates='studies')

    def __init__(self, study_id, user_id, admin=False, is_primary_contact=False,
            is_kimel_contact=False, is_study_RA=False, does_qc=False):
        self.study_id = study_id
        self.user_id = user_id
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
    code = db.Column('code', db.String(32))

    site = db.relationship('Site', back_populates='studies')
    study = db.relationship('Study', back_populates='sites')

    def __init__(self, study_id, site_id, uses_redcap=False, code=None):
        self.study_id = study_id
        self.site_id = site_id
        self.uses_redcap = uses_redcap
        self.code = code

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

    def __init__(self, user_id, timepoint_id, description):
        self.user_id = user_id
        self.timepoint_id = timepoint_id
        self.description = description
        self.timestamp = datetime.datetime.now(FixedOffsetTimezone(offset=TZ_OFFSET))

    def __repr__(self):
        return "<IncidentalFinding {} for {} found by User {}>".format(
                self.id, self.timepoint_id, self.user_id)

class MetricValue(db.Model):
    __tablename__ = 'scan_metrics'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False)
    metrictype_id = db.Column('metric_type', db.Integer,
            db.ForeignKey('metrictypes.id'), nullable=False)
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
