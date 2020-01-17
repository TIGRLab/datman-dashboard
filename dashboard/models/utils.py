import os
import json
import time
import logging

logger = logging.getLogger(__name__)


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
