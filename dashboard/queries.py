"""
Database queries used by the app
"""
import logging
import utils

from sqlalchemy import and_, func

from dashboard import db
from .models import Timepoint, Session, Scan, Study, Site, Metrictype, \
    MetricValue, Scantype, StudySite, AltStudyCode, User
import datman.scanid as scanid

logger = logging.getLogger(__name__)

def get_study(name=None, tag=None, site=None):
    if name:
        return Study.query.filter(Study.id == name).all()
    studies = StudySite.query.filter(StudySite.code == tag)
    if site:
        studies = studies.filter(StudySite.site_id == site)
    if not studies.all():
        studies = AltStudyCode.query.filter(AltStudyCode.code == tag)
        if site:
            studies = studies.filter(AltStudyCode.site_id == site)
    return studies.all()
    
def find_subjects(search_str):
    """
    Used by the dashboard's search bar
    """
    search_str = search_str.strip().upper()
    query = Timepoint.query.filter(func.upper(Timepoint.name).contains(
            search_str))
    return query.all()

def get_session(name, num):
    """
    Used by datman. Return a specific session or None
    """
    return Session.query.get((name, num))

def get_timepoint(name):
    """
    Used by datman. Return one timepoint or None
    """
    return Timepoint.query.get(name)


def find_sessions(search_str):
    """
    Used by the dashboard's search bar and so must work around fuzzy user
    input.
    """
    search_str = search_str.strip().upper()
    try:
        ident = scanid.parse(search_str)
    except:
        # Not a proper ID, try fuzzy search for name match
        query = Session.query.filter(func.upper(Session.name).contains(
                search_str))
    else:
        if ident.session:
            query = Session.query.filter(and_(func.upper(Session.name) ==
                    ident.get_full_subjectid_with_timepoint(),
                    Session.num == ident.session))
            if not query.count():
                ident.session = None

        if not ident.session:
            query = Session.query.filter((func.upper(Session.name) ==
                    ident.get_full_subjectid_with_timepoint()))

    return query.all()


def get_scan(scan_name, timepoint=None, session=None):
    """
    Used by datman. Return a list of matching scans or an empty list
    """
    query = Scan.query.filter(Scan.name == scan_name)
    if timepoint:
        query = query.filter(Scan.timepoint == timepoint)
    if session:
        query = query.filter(Scan.repeat == session)
    return query.all()


def find_scans(search_str):
    """
    Used by the dashboard's search bar and so must work around fuzzy user
    input.
    """
    search_str = search_str.strip().upper()
    try:
        ident, tag, series, _ = scanid.parse_filename(search_str)
    except:
        try:
            ident = scanid.parse(search_str)
        except:
            # Doesnt match a file name or a subject ID so fuzzy search
            # for...
            # matching scan name
            query = Scan.query.filter(func.upper(Scan.name).contains(
                    search_str))
            if query.count() == 0:
                # or matching subid
                query = Scan.query.filter(func.upper(Scan.timepoint).contains(
                        search_str))
            if query.count() == 0:
                # or matching tags
                query = Scan.query.filter(func.upper(Scan.tag).contains(
                        search_str))
            if query.count() == 0:
                # or matching series description
                query = Scan.query.filter(func.upper(Scan.description).contains(
                        search_str))
        else:
            if ident.session:
                query = Scan.query.filter(and_(func.upper(Scan.timepoint) ==
                        ident.get_full_subjectid_with_timepoint(),
                        Scan.repeat == int(ident.session)))
                if not query.count():
                    ident.session = None

            if not ident.session:
                query = Scan.query.filter((func.upper(Scan.timepoint) ==
                        ident.get_full_subjectid_with_timepoint()))
    else:
        name = "_".join([ident.get_full_subjectid_with_timepoint_session(), tag, series])
        query = Scan.query.filter(func.upper(Scan.name).contains(name))

    return query.all()

def get_user(username):
    query = User.query.filter(func.lower(User._username).contains(
            func.lower(username)))
    return query.all()

def query_metric_values_byid(**kwargs):
    """Queries the database for metrics matching the specifications.
        Arguments are lists of strings containing identifying names

        Example:
        rows = query_metric_value(Studies=['ANDT','SPINS'],
                                  ScanTypes=['T1'],
                                  MetricTypes=['SNR'])

    """
    # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {'studies': 'Study.id',
               'sites': 'Site.id',
               'sessions': 'Session.id',
               'scans': 'Scan.id',
               'scantypes': 'ScanType.id',
               'metrictypes': 'MetricType.id'}

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning('Ignoring invalid filter keys provided:{}'
                       .format(bad_keys))

    q = db.session.query(MetricValue)
    q = q.join(MetricType, MetricValue.metrictype)
    q = q.join(Scan, MetricValue.scan)
    q = q.join(ScanType, Scan.scantype)
    q = q.join(Session_Scan, Scan.sessions)
    q = q.join(Session, Session_Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)
    q = q.filter(Scan.bl_comment == None)

    for key in good_keys:
        if kwargs[key]:
            q = q.filter(eval(filters[key]).in_(kwargs[key]))
    q = q.order_by(Session.name)
    logger.debug('Query string: {}'.format(str(q)))

    result = q.all()

    return(result)


def query_metric_values_byname(**kwargs):
    """Queries the database for metrics matching the specifications.
        Arguments are lists of strings containing identifying names

        Example:
        rows = query_metric_value(Studies=['ANDT','SPINS'],
                                  ScanTypes=['T1'],
                                  MetricTypes=['SNR'])

    """
    # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {'studies': 'Study.nickname',
               'sites': 'Site.name',
               'sessions': 'Session.name',
               'scans': 'Scan.name',
               'scantypes': 'ScanType.name',
               'metrictypes': 'MetricType.name',
               'isphantom': 'Session.is_phantom'}

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning('Ignoring invalid filter keys provided:{}'
                       .format(bad_keys))

    q = db.session.query(MetricValue)
    q = q.join(MetricType, MetricValue.metrictype)
    q = q.join(Scan, MetricValue.scan)
    q = q.join(ScanType, Scan.scantype)
    q = q.join(Session_Scan, Scan.sessions)
    q = q.join(Session, Session_Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)
    q = q.filter(Scan.bl_comment == None)

    for key in good_keys:
        q = q.filter(eval(filters[key]).in_(kwargs[key]))

    q = q.order_by(Session.name)

    logger.debug('Query string: {}'.format(str(q)))

    result = q.all()

    return(result)


def query_metric_types(**kwargs):
    """Query the database for metric types fitting the specifications"""
        # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {'studies': 'Study.id',
               'sites': 'Site.id',
               'scantypes': 'ScanType.id',
               'metrictypes': 'MetricType.id'}

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning('Ignoring invalid filter keys provided: {}'
                       .format(bad_keys))

    q = db.session.query(Study, Site, Scantype, Metrictype) \
          .join(Study.sites) \
          .join(Study.scantypes) \
          .join(Scantype.metrictypes) \
          .distinct()

    for key in good_keys:
        if kwargs[key]:  # Don't add the filter if the option is empty
            q = q.filter(eval(filters[key]).in_(kwargs[key]))

    logger.debug('Query string: {}'.format(str(q)))
    result = q.all()

    return(result)
