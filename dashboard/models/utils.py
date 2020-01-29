"""Functions and classes for use in dashboard.models
"""

import os
import operator
import json
import time
import logging
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm.collections import MappedCollection, collection
import flask_apscheduler

from dashboard import scheduler

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


def schedule_email(email_func, input_args):
    """Send an email from the server side.

    If an automated email is fired from code that may be run on the client
    side then it should be wrapped by this function. This will add a scheduler
    job that fires instantly to ensure it executes server side (or just send it
    if it's already server side).

    NOTE: We're using scheduler.add_job directly and not
    dashboard.monitors.add_monitor because monitors often need classes from
    the models and using add_monitor would introduce circular dependencies.
    """
    if isinstance(scheduler, flask_apscheduler.APScheduler):
        # You're already executing on the server side so just send the email
        email_func(*input_args)
        return
    scheduler.add_job(uuid4().hex, email_func, trigger='date',
                      run_date=datetime.now(), args=input_args)
