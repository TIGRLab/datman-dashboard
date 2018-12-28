"""Location for utility functions"""
import logging
import os
from subprocess import Popen, STDOUT, PIPE

from github import Github

from dashboard import GITHUB_OWNER, GITHUB_REPO
import datman.config

DM_QC_TODO = '/archive/code/datman/bin/dm-qc-todo.py'
logger = logging.getLogger(__name__)
logger.info('loading utils')

class TimeoutError(Exception):
    pass

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
    study = scan.session.timepoint.studies.values()[0].id
    nii_folder = get_study_path(study, folder='nii')
    fname = "_".join([scan.name, scan.description + ".nii.gz"])

    full_path = os.path.join(nii_folder, scan.timepoint, fname)
    if not os.path.exists(full_path):
        full_path = full_path.replace(".nii.gz", ".nii")

    return full_path
