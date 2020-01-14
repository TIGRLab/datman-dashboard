import os
import glob
import shutil
import logging

from github import Github
from flask import current_app, flash
from ..models import Study

import datman.config
import datman.scanid

logger = logging.getLogger(__name__)


def search_issues(token, timepoint):
    github_owner = current_app.config['GITHUB_OWNER']
    github_repo = current_app.config['GITHUB_REPO']
    search_string = "{} repo:{}/{}".format(
        timepoint, github_owner, github_repo)
    try:
        issues = Github(token).search_issues(search_string)
    except Exception:
        return None
    result = sorted(issues, key=lambda x: x.created_at)
    return result


def handle_issue(token, issue_form, study_id, timepoint):
    title = clean_issue_title(issue_form.title.data, timepoint)
    study = Study.query.get(study_id)

    staff_member = study.choose_staff_contact()
    if staff_member:
        assigned_user = staff_member.username
    else:
        assigned_user = None

    try:
        make_issue(token, title, issue_form.body.data, assign=assigned_user)
    except Exception as e:
        logger.error("Failed to create a GitHub issue for {}. "
                     "Reason: {}".format(timepoint, e))
        flash("Failed to create issue '{}'".format(title))
    else:
        flash("Issue '{}' created!".format(title))


def clean_issue_title(title, timepoint):
    title = title.rstrip()
    if not title:
        title = timepoint
    elif title.endswith('-'):
        title = title[:-1].rstrip()
    elif timepoint not in title:
        title = timepoint + " - " + title
    return title


def make_issue(token, title, body, assign=None):
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
    owner = current_app.config['GITHUB_OWNER']
    repo = current_app.config['GITHUB_REPO']
    try:
        repo = Github(token).get_user(owner).get_repo(repo)
    except Exception as e:
        raise Exception("Can't retrieve github issues repo. {}".format(e))
    return repo


def delete_timepoint(timepoint):
    config = datman.config.config(study=timepoint.get_study().id)

    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons', 'qc']:
        delete(config, path_key, folder=str(timepoint))

    for num in timepoint.sessions:
        delete(config,
               'dicom',
               files=['{}.zip'.format(str(timepoint.sessions[num]))])
        delete(config, 'resources', folder=str(timepoint.sessions[num]))
        delete(config,
               'std',
               files=[scan.name for scan in timepoint.sessions[num].scans])

    if not timepoint.bids_name:
        return

    delete_bids(config, timepoint.bids_name, timepoint.bids_session)


def delete_session(session):
    config = datman.config.config(study=session.get_study().id)

    files = [scan.name for scan in session.scans]
    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons']:
        delete(config, path_key, folder=str(session.timepoint), files=files)

    delete(config, 'dicom', files=['{}.zip'.format(str(session))])
    delete(config, 'resources', folder=str(session))
    delete(config, 'std', files=files)

    timepoint = session.timepoint
    if not timepoint.bids_name:
        return

    for scan in session.scans:
        delete_bids(config, timepoint.bids_name, timepoint.bids_session, scan)


def delete_scan(scan):
    config = datman.config.config(study=scan.get_study().id)

    for path_key in ['dcm', 'nii', 'mnc', 'nrrd', 'jsons']:
        delete(config, path_key, folder=str(scan.timepoint), files=[scan.name])

    delete(config, 'std', files=[scan.name])

    if not scan.bids_name:
        return

    timepoint = scan.session.timepoint
    delete_bids(config, timepoint.bids_name, timepoint.bids_session, scan)


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
        shutil.rmtree(path)
        return

    for item in files:
        matches = glob.glob(os.path.join(path, item + "*"))
        for match in matches:
            os.remove(match)

    if not os.listdir(path):
        os.rmdir(path)


def delete_bids(config, subject, session, scan=None):
    try:
        bids = config.get_path('bids')
    except Exception:
        return

    subject_folder = os.path.join(bids, 'sub-{}'.format(subject))
    session_folder = os.path.join(subject_folder, 'ses-{}'.format(session))

    if not scan:
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
            if not os.listdir(subject_folder):
                os.rmdir(subject_folder)
        return

    if not scan.bids_name:
        return

    bids_file = datman.scanid.parse_bids_filename(scan.bids_name)
    sub_dirs = []
    sub_dirs.append(subject_folder)
    sub_dirs.append(session_folder)
    for path, dirs, files in os.walk(session_folder):
        for dir in dirs:
            sub_dirs.append(os.path.join(path, dir))

        for item in files:
            if bids_file == item:
                full_path = os.path.join(path, item)
                os.remove(full_path)

    # Clean up any folders that may now be empty
    for dir in reversed(sub_dirs):
        try:
            os.rmdir(dir)
        except OSError:
            pass
