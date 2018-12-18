#!/usr/bin/env python
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
import datman.utils
import datman.config
import datman.scanid
from dashboard.docopt import docopt
from dashboard import db
from dashboard.models import Study, Session, Scan, MetricType, MetricValue, Session_Scan


logger = logging.getLogger(__name__)


root_dir = "/archive/data/"

config = datman.config.config()

num_in_project = 0
num_success = 0


def main():
    arguments = docopt(__doc__)
    arg_project = arguments['<project>']
    arg_subject = arguments['<subject>']
    quiet = arguments['--quiet']
    verbose = arguments['--verbose']
    debug = arguments['--debug']
    dryrun = arguments['--dry-run']

    logger.setLevel(logging.WARN)
    if quiet:
        logger.setLevel(logging.ERROR)
    if verbose:
        logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    logger.addHandler(ch)

    #  Find all relevant QC metric files in the filesystem
    #  exclusions = ["STOPPD", "DBDC", "RTMSWM", "PASD", "COGBDY", "VIPR", \
    #  "DTI3T", "DTI15T", "PACTMD", "COGBDO", "SPINS", "code", "README.md"]
    exclusions = ["code", "README.md"]#, "SPINS", "DTI3T", "STOPPD", "PACTMD"]
    if arg_project:  # Use specified project, otherwise all projects in 'data'
        projects = [arg_project]
    else:
        projects = os.listdir(root_dir)
        projects = filter(lambda dir: dir not in exclusions, projects)

    for project in projects:
        global num_in_project
        global num_success
        num_in_project = 0
        num_success = 0
        logger.info("Processing project {}".format(project))
        qc_dir = root_dir + project + "/qc/"
        if os.path.isdir(qc_dir):
            # Ignore these files in a project's "qc" folder
            exclusions = ["subject-qc.db", "checklist.csv", "logs", "phantom",
                          "papaya.js", "papaya.css", "index.html"]
            if arg_subject: # Use specified subject, otherwise all subjects
                subjects = [arg_subject]
            else:
                subjects = os.listdir(qc_dir)
                subjects = filter(lambda dir: dir not in exclusions, subjects)
                logger.debug("Subjects in this project: {}".format(str(subjects)))
            for subject in subjects:
                session = add_session(subject)
                if not session:
                    continue
                subj_dir = qc_dir + subject
                # Use all .csv files in a subject folder
                datafiles = filter(lambda file: file.endswith(".csv"),
                                   os.listdir(subj_dir))
                datafiles = filter(lambda file: file.endswith(("_stats.csv", "_scanlengths.csv", "_qascript_fmri.csv",
                                    "_qascript_dti.csv", "_qascripts_bold.csv",
                                    "_qascripts_dti.csv", "_spikecount.csv",
                                    "_adni-contrasts.csv")), datafiles)
                num_in_project += len(datafiles)
                for df in datafiles:
                    df_path = subj_dir + "/" + df
                    #logger.info("Processing file {}".format(df))
                    parse_datafile(df, df_path, session)
        logger.info("{}/{} files processed successfully".format(num_success, num_in_project))


def add_session(session_name):
    logger.debug('Checking session:{}'.format(session_name))
    try:
        is_phantom = datman.scanid.is_phantom(session_name)
        ident = datman.scanid.parse(session_name)
        # sep_df = df.split("_")
        # is_phantom = False
        # if sep_df[2] == "PHA":
        #     proj_name, site_name, subj_name, tag = sep_df[0], sep_df[1], \
        #         sep_df[2] + "_" + sep_df[3], sep_df[4]
        #     is_phantom = True
        # else:
        #     proj_name, site_name, subj_name, timepoint, repeat, tag = sep_df[0], sep_df[1], \
        #         sep_df[2], sep_df[3], sep_df[4], sep_df[5]
    except datman.scanid.ParseException:
        logger.error("{} is not named properly".format(session_name))
        return

    study_name = config.map_xnat_archive_to_project(session_name)

    q = Study.query.filter(Study.nickname == study_name)
    if q.count() < 1:
        logger.error('Study:{} not found, skipping'.format(study_name))
        return
    study = q.first()

    site = [s for s in study.sites if s.site.name == ident.site]
    if not site:
        logger.error('Site:{} not valid for Study:{}, skipping.'
                     .format(ident.site, study.nickname))
        return

    site = site[0].site

    session_name = ident.get_full_subjectid_with_timepoint()
    query = Session.query.filter(Session.name == session_name)

    if not query.count():
        logger.info('Adding new session with name:{}'.format(session_name))
        session = Session()
        session.name = session_name
        session.study = study
        session.site = site
        session.is_phantom = is_phantom
        session.is_repeated = False
        session.repeat_count = 1

    else:
        session = query.first()

    logger.info('Checking checklist')
    checklist_comment = datman.utils.check_checklist(session_name)
    if checklist_comment:
        logger.info('Checklist comment {} found'.format(checklist_comment))
        session.cl_comment = checklist_comment

    db.session.add(session)
    db.session.commit()
    return(session)

def add_scan(session, filename):
    """Add or return a scan object"""
    try:
        ident, tag, series, description = datman.scanid.parse_filename(filename)
        # metadata descriptions also have metric type inluded
        description = description.split('_')[0]

    except datman.scanid.ParseException:
        logger.error("{} is not named properly".format(filename))
        return
    scan_name = '{}_{}_{}'.format(ident.get_full_subjectid_with_timepoint_session(),
                                     tag, series)

    scantype = [s for s in session.study.scantypes if s.name == tag]
    if not scantype:
        logger.error('Scantype:{} not found in study:{}.'
                     .format(tag, session.study.nickname))
        return
    else:
        scantype = scantype[0]

    query = Scan.query.filter(Scan.name == scan_name)
    if query.count():
        scan = query.first()
    else:
        logger.info('Adding new scan with name{}:'.format(scan_name))
        scan = Scan()
        session_scan = Session_Scan()

        scan.name = scan_name
        scan.scantype = scantype
        scan.series_number = series
        scan.description = description

        if ident.session:
            scan.repeat_number = int(ident.session)

        # Needed to set an ID for a new scan, so an entry into session_scans
        # can be made
        db.session.add(scan)
        db.session.flush()

        # Creates an entry in session_scans table for a new scan. Cannot tell
        # from here whether it's a link or not, so for now it just uses the table
        # default of is_primary='False'. This will need to be fixed with a
        # (probably large) refactoring, which is advisable anyway since the script
        # is duplicating a lot of code from datman/dashboard.py and is just
        # generally kind of hack-y
        session_scan.scan_id = scan.id
        session_scan.session_id = session.id
        session_scan.scan_name = scan_name


    logger.info('Checking blacklist')
    blacklist_name = '{}_{}'.format(scan_name, description)
    blacklist_comment = datman.utils.check_blacklist(blacklist_name)

    if blacklist_comment:
        logger.info('Blacklist comment {} found'.format(blacklist_comment))
        scan.bl_comment = blacklist_comment

    db.session.add(scan)
    db.session.commit()
    return(scan)

def add_metric_value(scan, metrictype, value):
    """Checks to see if metric value exists in the database, adds if not
    If value does exist, but is of a different value it updates the record"""
    assert isinstance(scan, Scan)
    assert isinstance(metrictype, MetricType)

    qry = MetricValue.query.filter(MetricValue.scan_id == scan.id) \
        .filter(MetricValue.metrictype_id == metrictype.id)

    if qry.count():
        # entry already exists
        metricvalue = qry.first()
    else:
        metricvalue = MetricValue()
        metricvalue.scan = scan
        metricvalue.metrictype = metrictype
        db.session.add(metricvalue)

    metricvalue.value = value
    db.session.commit()

def read_qcfile(path_to_file, space_delimited):
    return pd.read_csv(path_to_file,
                       delim_whitespace=space_delimited,
                       header=None).as_matrix()


def insert_from_rowfile(is_qascript, df_path, scan):
    try:
        if is_qascript:
            data = read_qcfile(df_path, True)
        else:
            data = read_qcfile(df_path, False)
            # Rotate data
            data = zip(data[0], data[1])
        for datapoint in data:
            st_id = int(scan.scantype.id)
            if MetricType.query.filter(MetricType.name == datapoint[0]).filter(MetricType.scantype_id == st_id).count():
                metrictype = MetricType.query.filter(MetricType.name == datapoint[0]).filter(MetricType.scantype_id == st_id).first()
            else:
                metrictype = MetricType()
                metrictype.name = datapoint[0]
                metrictype.scantype_id = scan.scantype_id
                db.session.add(metrictype)
                db.session.commit()

            add_metric_value(scan, metrictype, datapoint[1])

    except (IndexError, ValueError):
        logger.error("{} is missing data".format(df_path))


def insert_from_singleval(metrictype_name, has_header, df_path, scan):
    try:
        data = read_qcfile(df_path, False)
        st_id = int(scan.scantype.id)
        if MetricType.query.filter(MetricType.name == metrictype_name).filter(MetricType.scantype_id == st_id).count():
            metrictype = MetricType.query.filter(MetricType.name == metrictype_name).filter(MetricType.scantype_id == st_id).first()
        else:
            metrictype = MetricType()
            metrictype.name = metrictype_name
            metrictype.scantype_id = scan.scantype_id
            db.session.add(metrictype)
            db.session.commit()
        if has_header:
            value = data[0][1]
        else:
            value = data[0][0]
        add_metric_value(scan, metrictype, value)
    except (IndexError, ValueError):
        logger.error("{} is missing data".format(df_path))


def insert_from_contrasts(df_path, scan):
    try:
        data = read_qcfile(df_path, True)
        contrasts = ((data[1][0]/data[0][0],"c1"), (data[2][0]/data[0][0], "c2"),
                     (data[3][0]/data[0][0], "c3"), (data[4][0]/data[0][0], "c4"))
        for contrast in contrasts:
            st_id = int(scan.scantype.id)
            if MetricType.query.filter(MetricType.name == contrast[1]).filter(MetricType.scantype_id == st_id).count():
                metrictype = MetricType.query.filter(MetricType.name == contrast[1]).filter(MetricType.scantype_id == st_id).first()
            else:
                metrictype = MetricType()
                metrictype.name = contrast[1]
                metrictype.scantype = scan.scantype
                db.session.add(metrictype)
                db.session.commit()
            add_metric_value(scan, metrictype, contrast[0])
    except (IndexError, ValueError):
        logger.error("{} is missing data".format(df_path))

# Insert data associated with this file into the database
def parse_datafile(df, df_path, session):
    global config
    try:
        ident, tag, series, description = datman.scanid.parse_filename(df)
    except datman.scanid.ParseException:
        logger.error("{} is not named properly".format(df))
        return

    # Ignore unexpected files
    """recognized_files = ("_stats.csv", "_scanlengths.csv", "_qascript_fmri.csv",
                        "_qascript_dti.csv", "_qascripts_bold.csv",
                        "_qascripts_dti.csv", "_spikecount.csv",
                        "_adni-contrasts.csv")
    if not df.endswith(recognized_files):
        return
    """
    logger.info('Parsing file:{}'.format(df))
    # Get project, site, and subject from filename
    scan = add_scan(session, df)
    if not scan:
        return

    # Parsing differs depending on format of csv file
    if df.endswith("_stats.csv"):
        insert_from_rowfile(False, df_path, scan)
    elif df.endswith("_scanlengths.csv"):
        insert_from_singleval("ScanLength", True, df_path, scan)
    elif df.endswith("_spikecount.csv"):
        insert_from_singleval("Spikecount", False, df_path, scan)
    elif df.endswith("_adni-contrasts.csv"):
        insert_from_contrasts(df_path, scan)
    elif df.endswith("_qascript_fmri.csv") or df.endswith("_qascript_dti.csv") or df.endswith("_qascripts_bold.csv") or df.endswith("_qascripts_dti.csv"):
        insert_from_rowfile(True, df_path, scan)
    logger.info("done")
    # Add the new row to the database
    db.session.commit()
    global num_success
    num_success += 1
    logger.debug('Parsed {} files'.format(num_success))

if __name__ == '__main__':
    logging.basicConfig()
    main()
