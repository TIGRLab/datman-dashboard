from app import db
from .models import Study, Site, Session, Scan, MetricType, \
    MetricValue, ScanType  # noqa: F401
import logging

logger = logging.getLogger(__name__)


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
    q = q.join(Session, Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)

    for key in good_keys:
        if kwargs[key]:
            q = q.filter(eval(filters[key]).in_(kwargs[key]))

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
    q = q.join(Session, Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)

    for key in good_keys:
        q = q.filter(eval(filters[key]).in_(kwargs[key]))

    logger.debug('Query string: {}'.format(str(q)))
    q = q.limit(1000)

    result = q.all()

    return(result)


def query_metric_types(**kwargs):
    """Query the database for metric types fitting the specifictions"""
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
        logger.warning('Ignoring invalid filter keys provided:{}'
                       .format(bad_keys))

    q = db.session.query(Study, Site, ScanType, MetricType) \
          .join(Study.sites) \
          .join(Study.scantypes) \
          .join(ScanType.metrictypes) \
          .distinct()

    for key in good_keys:
        if kwargs[key]:  # Don't add the filter if the option is empty
            q = q.filter(eval(filters[key]).in_(kwargs[key]))

    logger.debug('Query string: {}'.format(str(q)))
    result = q.all()

    return(result)
