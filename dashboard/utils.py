"""Location for utility functions (including those that might need datman)
"""
import os
import json
import time
import glob
import shutil
import logging

from dashboard import GITHUB_OWNER, GITHUB_REPO
import datman.config

logger = logging.getLogger(__name__)


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
