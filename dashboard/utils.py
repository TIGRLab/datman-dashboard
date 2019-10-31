"""Location for utility functions"""
import os
import json
import time
import glob
import logging
from threading import Thread

from github import Github

from dashboard import GITHUB_OWNER, GITHUB_REPO
import datman.config
import datman.scanid

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def async_exec(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def search_issues(token, timepoint):
    search_string = "{} repo:{}/{}".format(timepoint, GITHUB_OWNER, GITHUB_REPO)
    try:
        issues = Github(token).search_issues(search_string)
    except:
        return None
    result = sorted(issues, key=lambda x: x.created_at)
    return result


def get_issue(token, issue_num=None):
    if not issue_num:
        return None
    try:
        repo = get_issues_repo(token)
        issue = repo.get_issue(issue_num)
    except Exception as e:
        logger.error("Can't retrieve issue {}. Reason: {}".format(issue_num, e))
        issue = None
    return issue


def create_issue(token, title, body, assign=None):
    try:
        repo = get_issues_repo(token)
        if assign:
            issue = repo.create_issue(title, body, assignee=assign)
        else:
            # I thought a default of None would be a clever way to avoid needing
            # an if/else here but it turns out 'assignee' will raise a
            # mysterious exception when set to None :( So... here we are
            issue = repo.create_issue(title, body)
    except Exception as e:
        raise Exception("Can't create new issue '{}'. Reason: {}".format(title,
                e))
    return issue


def get_issues_repo(token):
    try:
        repo = Github(token).get_user(GITHUB_OWNER).get_repo(GITHUB_REPO)
    except Exception as e:
        raise Exception("Can't retrieve github issues repo. {}".format(e))
    return repo


def get_study_path(study, folder=None):
    """
    Returns the full path to the study on the file system.

    If folder is supplied and is defined in study config
    then path to the folder is returned instead.
    """
    cfg = datman.config.config()
    if folder:
        try:
            path = cfg.get_path(folder, study)
        except Exception as e:
            logger.error("Failed to find folder {} for study {}. Reason: {}"
                    "".format(folder, study, e))
            path = None
        return path

    try:
        path = cfg.get_study_base(study=study)
    except Exception as e:
        logger.error("Failed to find path for {}. Reason: {}".format(study, e))
        path = None
    return path


def get_nifti_path(scan):
    study = scan.get_study().id
    nii_folder = get_study_path(study, folder='nii')
    fname = "_".join([scan.name, scan.description + ".nii.gz"])

    full_path = os.path.join(nii_folder, scan.timepoint, fname)
    if not os.path.exists(full_path):
        full_path = full_path.replace(".nii.gz", ".nii")

    return full_path


def read_json(json_file):
    with open(json_file, "r") as fp:
        contents = json.load(fp)
    return contents


def file_timestamp(file_path):
    epoch_time = os.path.getctime(file_path)
    return time.ctime(epoch_time)


def get_software_version(json_contents):
    try:
        software_name = json_contents['ConversionSoftware']
    except KeyError:
        software_name = "Name Not Available"
    try:
        software_version = json_contents['ConversionSoftwareVersion']
    except KeyError:
        software_version = "Version Not Available"
    return software_name + " - " + software_version


def update_json(scan, contents):
    scan.json_contents = contents
    scan.save()

    updated_jsons = get_study_path(scan.get_study().id, "jsons")
    json_folder = os.path.join(updated_jsons, scan.timepoint)
    try:
        os.makedirs(json_folder)
    except:
        pass
    new_json = os.path.join(json_folder, os.path.basename(scan.json_path))

    with open(new_json, "w") as out:
        json.dump(contents, out)

    os.remove(scan.json_path)
    os.symlink(os.path.join(os.path.relpath(json_folder,
                                            os.path.dirname(scan.json_path)),
                            os.path.basename(scan.json_path)),
               scan.json_path)


def update_header_diffs(scan):
    site = scan.session.timepoint.site_id
    config = datman.config.config(study=scan.get_study().id)

    try:
        tolerance = config.get_key("HeaderFieldTolerance", site=site)
    except:
        tolerance = {}
    try:
        ignore = config.get_key("IgnoreHeaderFields", site=site)
    except:
        ignore = []

    tags = config.get_tags(site=site)
    try:
        qc_type = tags.get(scan.tag, "qc_type")
    except KeyError:
        check_bvals = False
    else:
        check_bvals = qc_type == 'dti'

    scan.update_header_diffs(ignore=ignore, tolerance=tolerance,
                             bvals=check_bvals)


@async_exec
def delete_session(session):
    config = datman.config.config(study=session.get_study().id)

    files = [scan.name for scan in session.scans]
    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons']:
        delete(config, path_key, folder=str(session.timepoint), files=files)

    delete(config, 'dicom', files=['{}.zip'.format(str(session))])
    delete(config, 'resources', folder=str(session))

    timepoint = session.timepoint
    if not timepoint.bids_name:
        return

    for scan in session.scans:
        delete_bids(config, timepoint.bids_name, timepoint.bids_session, scan)


@async_exec
def delete_scan(scan):
    config = datman.config.config(study=scan.get_study().id)

    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons']:
        delete(config, path_key, folder=str(scan.timepoint), files=[scan.name])

    if not scan.bids_name:
        return

    timepoint = scan.session.timepoint
    delete_bids(config, timepoint.bids_name, timepoint.bids_session, scan)


@async_exec
def delete_timepoint(timepoint):
    config = datman.config.config(study=timepoint.get_study().id)

    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons', 'qc']:
        delete(config, path_key, folder=str(timepoint))

    for num in timepoint.sessions:
        delete(config, 'dicom', folder=str(timepoint.sessions[num]))
        delete(config, 'resources', folder=str(timepoint.sessions[num]))

    if not timepoint.bids_name:
        return

    delete_bids(config, timepoint.bids_name, timepoint.bids_session)


def delete(config, key, folder=None, files=None):
    if files and not isinstance(files, list):
        files = [files]

    try:
        path = config.get_path(key)
    except Exception:
        return

    if folder:
        path = os.path.join(path, folder)

    if not os.path.exists(path):
        return

    if not files:
        print("Deleting {}".format(path))
        return

    for item in files:
        matches = glob.glob(os.path.join(path, item + "*"))
        for match in matches:
            print("Deleting {}".format(match))

    if not os.listdir(path):
        print("Deleting empty directory {}".format(path))


def delete_bids(config, subject, session, scan=None):
    try:
        bids = config.get_path('bids')
    except Exception:
        return

    bids_folder = os.path.join(bids,
                               'sub-{}'.format(subject),
                               'ses-{}'.format(session))

    if not scan:
        if os.path.exists(bids_folder):
            print("Deleting {}".format(bids_folder))
        return

    if not scan.bids_name:
        return

    bids_file = datman.scanid.parse_bids_filename(scan.bids_name)
    for path, _, files in os.walk(bids_folder):
        for item in files:
            if bids_file == item:
                full_path = os.path.join(path, item)
                print("Deleting {}".format(full_path))

    if not os.listdir(bids_folder):
        print("Deleting empty directory {}".format(bids_folder))
