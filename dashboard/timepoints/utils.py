import os
import glob
import shutil

from github import Github
from flask import current_app

import datman.config
import datman.scanid


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
