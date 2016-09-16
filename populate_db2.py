
"""Populate the dashboard database with Project, Site and Scantype information

Usage:
    populate_db2 [options] <config.yml> <dashboard.sqlite>

Arguments:
    <config.yml>        Configuration file in yml format
    <dashboard.sqlite>  Database for the dashboard

Options:
    --quiet     Don't print warnings
    --verbose   Print warnings
    --help      Print help

DETAILS

Reads from yml config file to determine current projects and their locations.
Looks in each project/metadata folder for a project_settings.yml file to get
information on Sites and expected scantypes.

Populates the database with this information.

Example:
    populate_db2 ${DATMAN_ASSESTSDIR}/tigrlab_config.yaml dashboard.sqlite
"""
import logging
import yaml
import os

from docopt import docopt

from app.database import db_session
from app.models import Study, Site, Session, Scan, ScanType, MetricType, MetricValue

import datman as dm
import datman.utils
import datman.scanid

logger = logging.getLogger(__name__)

def read_yaml(file):
    """Read and parse a yaml file.

       Arguments:
         file: file path to a valid yaml file
     """
     try:
         with open(file, 'r') as stream:
             return yaml.load(stream)
     except:
         logger.error('Invalid yaml file: {}'.format(file))
         raise

def main(config_yml, database_file):
    config = read_yaml(config_yml)

    #Check we have the required sections
    required_keys = ['Projects', 'ExportSettings']
    diffs = set(ExpectedKeys) - set(config.keys())
    if len(diffs) > 0:
        logger.error("""Invalid yaml file: {}.
                        {} keys not found.""".format(config_yml,
                                                     diffs))
        raise RuntimeError

if __name__ == '__main__':
    arguments       = docopt(__doc__)
    config_yml      = arguments['<config.yml>']
    database_file   = arguments['<database.sqlite>']
    VERBOSE         = arguments['--verbose']
    QUIET           = arguments['--quiet']

    if QUIET:
        logger.setLevel(logging.ERROR)

    if VERBOSE:
        logger.setLevel(logging.INFO)

    main()
