"""Functions and classes for use in dashboard.models
"""

import os
import operator
import json
import time
import logging
from uuid import uuid4
from datetime import datetime

import xnat
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


def schedule_email(email_func, input_args, input_kwargs=None):
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
                      run_date=datetime.now(), args=input_args,
                      kwargs=input_kwargs)


def update_xnat_usability(scan, current_app):
    """Push user QC into XNAT's 'usability' fields.

    Args:
        scan (:obj:`dashboard.models.Scan`): The series to push QC data for.
        current_app (:obj:`werkzeug.local.LocalProxy`): The current application
            context.
    """
    study = scan.get_study()
    site_settings = study.sites[scan.session.site.name]

    xnat_session = getattr(
        scan.session, site_settings.xnat_convention.lower() + "_name"
    )
    user, password = get_xnat_credentials(site_settings, current_app)
    with xnat.connect(site_settings.xnat_server,
                      user=user,
                      password=password) as xcon:
        project = xcon.projects[site_settings.xnat_archive]
        xnat_exp = project.experiments[xnat_session]
        xnat_scan = xnat_exp.scans[scan.series]

        if scan.flagged():
            xnat_scan.quality = 'questionable'
        elif scan.blacklisted():
            xnat_scan.quality = 'unusable'
        else:
            xnat_scan.quality = 'usable'
        xnat_scan.note = scan.qc_review.comment


def get_xnat_credentials(site_settings, current_app):
    """Retrieve the xnat username and password for a given study/site.

    Args:
        site_settings (:obj:`dashboard.models.StudySite`): A StudySite record
        current_app (:obj:`werkzeug.local.LocalProxy`): The current application
            context.
    """
    if current_app.config.get('XNAT_USER'):
        user = current_app.config.get('XNAT_USER')
        password = current_app.config.get('XNAT_PASS')
        return user, password

    try:
        with open(site_settings.xnat_credentials) as fh:
            contents = fh.readlines()
    except (FileNotFoundError, PermissionError) as e:
        logger.error("Failed to read XNAT credentials file "
                     f"{site_settings.xnat_credentials}. {e}")

    try:
        user = contents[0].strip()
        password = contents[1].strip()
    except (IndexError, AttributeError) as e:
        logger.error("Failed to parse XNAT credentials file "
                     f"{site_settings.xnat_credentials}. {e}")

    return user, password
