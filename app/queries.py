from .database import db_session
from .models import Study, Site, Session, Scan, MetricType, MetricValue, ScanType
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def query_metric_values_byid(**kwargs):
    """Queries the database for metrics matching the specifications.
        Arguments are lists of strings containing identifying names

        Example:
        rows = query_metric_value(Studies=['ANDT','SPINS'],
                                  ScanTypes=['T1'],
                                  MetricTypes=['SNR'])

    """
    # convert the argument keys to lowercase
    kwargs =  {k.lower(): v for k, v in kwargs.items()}

    filters = {'studies'        : 'Study.id',
               'sites'          : 'Site.id',
               'sessions'       : 'Session.id',
               'scans'          : 'Scan.id',
               'scantypes'      : 'ScanType.id',
               'metrictypes'    : 'MetricType.id'}

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning('Ignoring invalid filter keys provided:{}'.format(diffs))

    query_str = """db_session.query(MetricValue) \
                        .join(Site.studies) \
                        .join(Session) \
                        .join(Scan) \
                        .join(ScanType) \
                        .join(MetricValue) \
                        .join(MetricType)"""

    for key in good_keys:
        if kwargs[key]:
            query_str = query_str + '.filter({}.in_({}))'.format(filters[key],kwargs[key])

    query_str = query_str + '.all()'

    logger.debug('Query string: {}'.format(query_str))

    result = eval(query_str)

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
    kwargs =  {k.lower(): v for k, v in kwargs.items()}

    filters = {'studies'        : 'Study.name',
               'sites'          : 'Site.name',
               'sessions'       : 'Session.name',
               'scans'          : 'Scan.name',
               'scantypes'      : 'ScanType.name',
               'metrictypes'    : 'MetricType.name'}

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning('Ignoring invalid filter keys provided:{}'.format(diffs))

    query_str = """db_session.query(MetricValue) \
                        .join(Site.studies) \
                        .join(Session) \
                        .join(Scan) \
                        .join(ScanType) \
                        .join(MetricValue) \
                        .join(MetricType)"""

    for key in good_keys:
        query_str = query_str + '.filter({}.in_({}))'.format(filters[key],kwargs[key])

    query_str = query_str + '.all()'

    logger.debug('Query string: {}'.format(query_str))

    result = eval(query_str)

    return(result)
