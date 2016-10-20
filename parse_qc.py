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

root_dir = "/archive/data/"
config = dm.config.config(filename="/archive/code/datman/assets/tigrlab_config.yaml")


def main():
    arguments = docopt(__doc__)
    arg_project = arguments['<project>']
    arg_subject = arguments['<subject>']
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

    # Find all relevant QC metric files in the filesystem
    # exclusions = ["STOPPD", "DBDC", "RTMSWM", "PASD", "COGBDY", "VIPR", \
    # "DTI3T", "DTI15T", "PACTMD", "COGBDO", "SPINS", "code", "README.md"]
    exclusions = ["code", "README.md"]
    if arg_project:  # Use specified project, otherwise all projects in 'data'
        projects = [arg_project]
    else:
        projects = os.listdir(root_dir)
        projects = filter(lambda dir: dir not in exclusions, projects)

    for project in projects:
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

            for subject in subjects:
                subj_dir = qc_dir + subject
                # Use all .csv files in a subject folder
                datafiles = filter(lambda file: file.endswith(".csv"),
                                   os.listdir(subj_dir))
                for df in datafiles:
                    df_path = subj_dir + "/" + df
                    logger.info("Processing file {}".format(df))
                    parse_datafile(df, df_path)


def read_qcfile(path_to_file, space_delimited):
    return pd.read_csv(path_to_file,
                       delim_whitespace=space_delimited,
                       header=None).as_matrix()


def insert_from_rowfile(is_qascript, df_path):
    try:
        if is_qascript:
            data = read_qcfile(df_path, True)
        else:
            data = read_qcfile(df_path, False)
            # Rotate data
            data = zip(data[0], data[1])
        for datapoint in data:
            metricvalue = MetricValue()
            if MetricType.query.filter(MetricType.name == datapoint[0]).count() and MetricType.query.filter(MetricType.scantype_id == scan.scantype_id).count():
                metrictype = MetricType.query.filter(MetricType.name == datapoint[0]).filter(MetricType.scantype_id == scan.scantype_id).first()
            else:
                metrictype = MetricType()
                metrictype.name = datapoint[0]
                metrictype.scantype_id = scan.scantype_id
                db.session.add(metrictype)
            metricvalue.metrictype = metrictype
            metricvalue.value = datapoint[1]
            scan.metricvalues.append(metricvalue)
    except (IndexError, ValueError):
        logger.error("{} is missing data".format(df_path))


def insert_from_singleval(metrictype_name, df_path):
    try:
        data = read_qcfile(df_path, False)
        metricvalue = MetricValue()
        if MetricType.query.filter(MetricType.name == metrictype_name).count() and MetricType.query.filter(MetricType.scantype_id == scan.scantype_id).count():
            metrictype = MetricType.query.filter(MetricType.name == metrictype_name).filter(MetricType.scantype_id == scan.scantype_id).first()
        else:
            metrictype = MetricType()
            metrictype.name = metrictype_name
            metrictype.scantype_id = scan.scantype_id
            db.session.add(metrictype)
        metricvalue.metrictype = metrictype
        metricvalue.value = data[0][1]
        scan.metricvalues.append(metricvalue)
    except (IndexError, ValueError):
        logger.error("{} is missing data".format(df_path))

def insert_from_contrasts(df_path):
    pass  # TODO

# Insert data associated with this file into the database
def parse_datafile(df, df_path):
    global config
    # Ignore unexpected files
    recognized_files = ("_stats.csv", "_scanlengths.csv", "_qascript_fmri.csv",
                        "_qascript_dti.csv", "_qascripts_bold.csv",
                        "_qascripts_dti.csv", "_spikecount.csv",
                        "_adni-contrasts.csv")
    if not df.endswith(recognized_files):
        return

    # Get project, site, and subject from filename
    sep_df = df.split("_")
    is_phantom = False
    if sep_df[2] == "PHA":
        proj_name, site_name, subj_name, tag = sep_df[0], sep_df[1], \
            sep_df[2] + "_" + sep_df[3], sep_df[4]
        is_phantom = True
    else:
        proj_name, site_name, subj_name, tag = sep_df[0], sep_df[1], \
            sep_df[2], sep_df[5]

    study_name = config.map_xnat_archive_to_project(proj_name)
    # Get study object if it exists, or make one
    if Study.query.filter(Study.nickname == study_name).count():
        study = Study.query.filter(Study.nickname == study_name).first()
    else:
        logger.warning("Study {} does not exist in database; skipping.".format(study_name))
        return

    # Get session object if it exists, or make one
    session_name = proj_name + "_" + site_name + "_" + subj_name
    if Session.query.filter(Session.name == session_name).count():
        session = Session.query.filter(Session.name == session_name).first()
    else:
        session = Session()
        session.name = session_name
    study.sessions.append(session)

    # Ensure site is a possible site, and fetch the object
    possible_sites = study.sites
    for site in possible_sites:
        if site.name == site_name:
            session.site = site
    if not session.site:
        logger.warning("Site {} not associated with study {}; skipping.".format(site_name, proj_name))
        return

    # Get session object if it exists, or make one
    scan_name = session_name + "_" + tag
    if Scan.query.filter(Scan.name == scan_name).count():
        scan = Scan.query.filter(Scan.name == scan_name).first()
    else:
        scan = Scan()
        scan.name = scan_name
    session.scans.append(scan)

    # Ensure scantype is a possible scantype, and fetch the object
    possible_scantypes = study.scantypes
    for scantype in possible_scantypes:
        if scantype.name == tag:
            scan.scantype = scantype
    if not scan.scantype:
        logger.warning("Scantype {} not associated with study {}; skipping.".format(tag, proj_name))
        return

    # Parsing differs depending on format of csv file
    if df.endswith("_stats.csv"):
        insert_from_rowfile(is_qascript=False, df_path)
    elif df.endswith("_scanlengths.csv"):
        insert_from_singleval("ScanLength", df_path)
    elif df.endswith("_spikecount.csv"):
        insert_from_singleval("Spikecount", df_path)
    elif df.endswith("_adni-contrasts.csv"):
        insert_from_contrasts(df_path)
    elif df.endswith("_qascript_fmri.csv") or df.endswith("_qascript_dti.csv")
     or df.endswith("_qascripts_bold.csv") or df.endswith("_qascripts_dti.csv"):
        insert_from_rowfile(is_qascript=True, df_path)

    # Add the new row to the database
    db.session.commit()


if __name__ == '__main__':
    main()
