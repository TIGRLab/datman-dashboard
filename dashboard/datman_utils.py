"""Dashboard functionality that requires datman's config module.

Some parts of the dashboard need datman.config to locate things on the file
system but datman.config uses the dashboard's models. So to help prevent
circular references (and debug them when they happen) isolate all the
datman.config related code here.

This can safely be imported elsewhere but no dashboard related imports should
ever appear here

.. note:: This currently does not import correctly outside of an app context.
One consequence of this is that sphinx's automodule can't add it to the docs.
We have to solve the datman.config circular reference issues to fix this. :(
"""

import os
import shutil
import glob
import logging
import json
from collections import OrderedDict

import datman.config
import datman.scanid
from datman.exceptions import UndefinedSetting

logger = logging.getLogger(__name__)


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

    if files is None:
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
        for sub_dir in dirs:
            sub_dirs.append(os.path.join(path, sub_dir))

        for item in files:
            if bids_file == item:
                full_path = os.path.join(path, item)
                os.remove(full_path)

    # Clean up any folders that may now be empty
    for sub_dir in reversed(sub_dirs):
        try:
            os.rmdir(sub_dir)
        except OSError:
            pass


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

    scan.update_header_diffs(ignore=ignore,
                             tolerance=tolerance)


def get_manifests(timepoint):
    """Collects and organizes all QC manifest files for a timepoint.

    Args:
        timepoint (:obj:`dashboard.models.Timepoint`): A timepoint from the
            database.

    Returns:
        A dictionary mapping session numbers to a dictionary of input nifti
        files and their manifest contents.

        For example:
        {
            1: {nifti_1: nifti_1_manifest,
                nifti_2: nifti_2_manifest},
            2: {nifti_3: nifti_3_manifest}
         }
    """
    study = timepoint.get_study().id
    config = datman.config.config(study=study)
    try:
        qc_dir = config.get_path("qc")
    except UndefinedSetting:
        logger.error("No QC path defined for study {}".format(study))
        return {}

    qc_path = os.path.join(qc_dir, str(timepoint))
    found = {}
    for num in timepoint.sessions:
        session = timepoint.sessions[num]
        found[num] = {}

        manifests = glob.glob(
            os.path.join(qc_path, f"{session}_*_manifest.json")
        )

        for manifest in manifests:
            contents = read_json(manifest)

            _, _, _, description = datman.scanid.parse_filename(manifest)
            scan_name = os.path.basename(manifest).replace(
                f"{description}.json",
                ""
            ).strip("_")

            # Needed to ensure ordering respected
            ordered_contents = OrderedDict(
                sorted(contents.items(), key=lambda x: x[1].get("order", 999))
            )

            found[num][scan_name] = ordered_contents

    return found


def read_json(in_file):
    """Read a json file.

    Args:
        in_file (:obj:`str`): The full path the the json file to load.

    Returns:
        dict: A dictionary of the json contents or an error message.
    """
    with open(in_file, "r") as fh:
        try:
            contents = json.load(fh)
        except json.JSONDecodeError:
            contents = {
                "Error": {
                    in_file: "Unreadable manifest file."
                }
            }
    return contents
