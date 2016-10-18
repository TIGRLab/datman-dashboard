"""Parse QC files for a project or subject

Usage:
  parse_qc.py [options]
  parse_qc.py [options] <project>
  parse_qc.py [options] <project> <subject>

Arguments:
  <project>  Shortname for the study to process
  <subject>  Name of the subject to process

Options:
  -h --help     Print this page
  -q --quiet    Minimal reporting
  -v --verbose  More reporting
  -d --debug    Lots of reporting
  --dry-run     Perform a dryrun, dont enter anything into database
"""

import pandas as pd
import os
import sys
import logging
import datman as dm
from docopt import docopt
from app import db
from app.models import Study, Session, Scan, MetricType, MetricValue

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

def main():
    arguments = docopts(__doc__)
    project = arguments['<project>']
    subject = arguments['<subject>']
    quiet = arguments['--quiet']
    verbose = arguments['--verbose']
    debug = arguments['--debug']
    dryrun = arguments['--dry-run']

    if quiet:
        logger.setLevel(logging.ERROR)
    if verbose:
        logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)
