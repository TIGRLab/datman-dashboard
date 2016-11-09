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
from dashboard import db
from dashboard.models import Study, Session, Scan, MetricType, MetricValue

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

def main():
    arguments = docopt(__doc__)
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

    config = dm.config.config(filename='/scratch/twright/code/config/tigrlab_config.yaml',
                              system='local')

    if project:
        try:
            config.set_study_config(project)
            qc_dir = config.get_if_exists('study', ['paths', 'qc'])
            if not qc_dir:
                logger.error('Failed to identify qc folder')
                raise KeyError
        except KeyError:
            logger.error('Invalid project:{}'.format(project))
            raise
        if subject:
            parse_subject_qc(qc_dir, subject)
        else:
            parse_project_qc(qc_dir)
    else:
        for project in config.site_config['ProjectSettings'].keys():
            logger.info('Processing project:{}'.format(project))
            config.set_study_config(project)
            qc_dir = config.get_if_exists('study', ['paths', 'qc'])
            if not qc_dir:
                logger.warning('Failed to identify qc folder for project:{}'
                               .format(project))
                continue
            parse_project_qc(qc_dir)


def parse_project_qc(qc_dir):
    if not os.path.isdir(qc_dir):
        logger.error('Invalid QC dir:{}'.format(qc_dir))
        return
    for subject_dir in os.listdirs(qc_dir):
        parse_subject_qc(qc_dir, subject_dir)


def parse_subject_qc(qc_dir, subject):
    subject_path = os.path.join(qc_dir, subject)
    if not dm.scanid.is_scanid(subject):
        logger.warning('subject {} isnt valid').format(subject)
        return
    if not os.path.isdir(subject_path):
        logger.error('Invalid subject path:{}'.format(subject_path))
        return
