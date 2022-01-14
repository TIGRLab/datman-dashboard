"""Functions and classes for use in dashboard.models
"""

import os
import operator
import json
import time
import logging
from urllib.parse import quote, unquote
from uuid import uuid4
from datetime import datetime

import xnat
from sqlalchemy.orm.collections import MappedCollection, collection
import flask_apscheduler

from dashboard import scheduler
from dashboard.emails import async_exec

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


def update_xnat_usability(scan, app_config):
    """Update XNAT usability data for a scan.

    Args:
        scan (:obj:`dashboard.models.Scan`): The series to push QC data for.
        app_config (:obj:`dict`): Configuration of the current app instance,
            as retrieved from current_app.config
    """
    study = scan.get_study()
    site_settings = study.sites[scan.session.site.name]

    if not site_settings.xnat_url:
        logger.info(f"{study.id} - No xnat url. Skipping QC push to XNAT.")
        return

    exp_name = getattr(
        scan.session, site_settings.xnat_convention.lower() + "_name"
    )

    user, password = get_xnat_credentials(site_settings, app_config)

    if scan.flagged():
        quality = 'questionable'
    elif scan.blacklisted():
        quality = 'unusable'
    else:
        quality = 'usable'

    async_xnat_update(
        site_settings.xnat_url,
        user,
        password,
        site_settings.xnat_archive,
        exp_name,
        scan.series,
        scan.qc_review.comment,
        quality
    )


def get_xnat_credentials(site_settings, app_config):
    """Retrieve the xnat username and password for a given study/site.

    Args:
        site_settings (:obj:`dashboard.models.StudySite`): A StudySite record
        app_config (:obj:`dict`): Configuration of the current app instance,
            as retrieved from current_app.config
    """
    if not site_settings.xnat_credentials and app_config.get('XNAT_USER'):
        user = app_config.get('XNAT_USER')
        password = app_config.get('XNAT_PASS')
        return user, password

    if not site_settings.xnat_credentials:
        logger.info(
            f"No XNAT credentials provided for {site_settings.study.id}. "
            "QC will not be pushed to XNAT database."
        )
        return

    try:
        with open(site_settings.xnat_credentials) as fh:
            contents = fh.readlines()
    except (FileNotFoundError, PermissionError) as e:
        logger.error("Failed to read XNAT credentials file "
                     f"{site_settings.xnat_credentials}. {e}")
        raise e

    try:
        user = contents[0].strip()
        password = contents[1].strip()
    except (IndexError, AttributeError) as e:
        logger.error("Failed to parse XNAT credentials file "
                     f"{site_settings.xnat_credentials}. {e}")
        raise e

    return user, password


@async_exec
def async_xnat_update(xnat_url, user, password, xnat_archive, exp_name,
                      series_num, comment, quality):
    """Push usability data into XNAT.

    This will update XNAT in a separate thread to reduce waiting time for the
    user. Because it will run in another thread, database objects cannot be
    passed in as arguments.

    Args:
        xnat_url (str): The full URL to use for the XNAT server.
        user (str): The user to log in as.
        password (str): The password to log in with.
        xnat_archvie (str): The name of the XNAT archive that contains the
            experiment.
        exp_name (str): The name of the experiment on XNAT.
        series_num (int): The series number of the file to update.
        comment (str): The user's QC comment.
        quality (str): The quality label to apply based on whether data
            has been flagged, blacklisted or approved.
    """
    with xnat.connect(xnat_url, user=user, password=password) as xcon:
        project = xcon.projects[xnat_archive]
        xnat_exp = project.experiments[exp_name]
        matched = [item for item in xnat_exp.scans[:]
                   if item.id == str(series_num)]

        if not matched or len(matched) > 1:
            logger.error(f"Couldn't locate {exp_name} on XNAT server. "
                         "Usability will not be updated.")
            return

        xnat_scan = matched[0]
        xnat_scan.quality = quality
        if comment:
            # XNAT max comment length is 255 chars
            safe_comment = comment if len(quote(comment)) < 255 \
                else unquote(quote(comment)[0:243]) + " [...]"
            xnat_scan.note = safe_comment
