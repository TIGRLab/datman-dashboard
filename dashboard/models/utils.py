"""Functions and classes for use in dashboard.models
"""

import os
import operator
import json
import time
import logging

from sqlalchemy.orm.collections import MappedCollection, collection

logger = logging.getLogger(__name__)


class DictListCollection(MappedCollection):
    """Allows a relationship to be organized into a dictionary of lists
    """
    def __init__(self, key):
        super(DictListCollection, self).__init__(operator.attrgetter(key))

    @collection.internally_instrumented
    def __setitem__(self, key, value, _sa_initiator=None):
        if not super(DictListCollection, self).get(key):
            super(DictListCollection, self).__setitem__(key, [], _sa_initiator)
        super(DictListCollection, self).__getitem__(key).append(value)

    @collection.iterator
    def list_mod(self):
        """Allows sqlalchemy manage changes to the contents of the lists
        """
        all_records = []
        for sub_list in self.values():
            all_records.extend(sub_list)
        return iter(all_records)


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
