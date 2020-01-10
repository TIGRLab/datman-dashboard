"""Location for utility functions (including those that might need datman)
"""
import os
import json
import time
import glob
import shutil
import logging

from github import Github

from dashboard import GITHUB_OWNER, GITHUB_REPO
import datman.config

logger = logging.getLogger(__name__)


def get_issue(token, issue_num=None):
    if not issue_num:
        return None
    try:
        repo = get_issues_repo(token)
        issue = repo.get_issue(issue_num)
    except Exception as e:
        logger.error("Can't retrieve issue {}. Reason: {}".format(
            issue_num, e))
        issue = None
    return issue


def create_issue(token, title, body, assign=None):
    try:
        repo = get_issues_repo(token)
        if assign:
            issue = repo.create_issue(title, body, assignee=assign)
        else:
            # I thought a default of None would be a clever way to avoid
            # needing an if/else here but it turns out 'assignee' will raise a
            # mysterious exception when set to None :( So... here we are
            issue = repo.create_issue(title, body)
    except Exception as e:
        raise Exception("Can't create new issue '{}'. Reason: {}".format(
            title, e))
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
    except FileExistsError:
        pass
    new_json = os.path.join(json_folder, os.path.basename(scan.json_path))

    with open(new_json, "w") as out:
        json.dump(contents, out)

    os.remove(scan.json_path)
    os.symlink(
        os.path.join(
            os.path.relpath(json_folder, os.path.dirname(scan.json_path)),
            os.path.basename(scan.json_path)), scan.json_path)


def update_header_diffs(scan):
    site = scan.session.timepoint.site_id
    config = datman.config.config(study=scan.get_study().id)

    try:
        tolerance = config.get_key("HeaderFieldTolerance", site=site)
    except Exception:
        tolerance = {}
    try:
        ignore = config.get_key("IgnoreHeaderFields", site=site)
    except Exception:
        ignore = []

    tags = config.get_tags(site=site)
    try:
        qc_type = tags.get(scan.tag, "qc_type")
    except KeyError:
        check_bvals = False
    else:
        check_bvals = qc_type == 'dti'

    scan.update_header_diffs(ignore=ignore,
                             tolerance=tolerance,
                             bvals=check_bvals)
