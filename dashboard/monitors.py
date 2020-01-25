#!/usr/bin/env python
"""Utility functions for adding and managing scheduled jobs.

This script contains a collection of functions that can be used to run
scheduled jobs on the dashboard's server. Each scheduled job requires two
pieces:
    1) A 'check' function that will run at the scheduled time and that does
       the actual work.
    2) A 'monitor' function that packages up the check function, any arguments
       it needs, and a date/time and submits it to the server.

NOTE: If a monitor is used by a view function in a blueprint it should be
put in a 'monitors' file inside the blueprint rather than here.
"""
import logging
from uuid import uuid4
from datetime import datetime, timedelta

from dashboard import scheduler
from .models import Session
from .emails import missing_redcap_email
from .exceptions import MonitorException

logger = logging.getLogger(__name__)


def add_monitor(check_function,
                input_args,
                input_kwargs=None,
                job_id=None,
                days=None,
                hours=None,
                minutes=None):
    """Add a job to be run on the server at a scheduled time.

    Args:
        check_function (:obj:`function`): The function that will run at the
            scheduled day and time.
        input_args (Any): Arguments to feed in to check_function at runtime
        input_kwargs (Any, optional): Optional args to feed in to
            check_function at runtime.
        job_id (:obj:`str`, optional): A unique identifier for the job
        days (int, optional): Number of days to add to the current time when
            setting the run date.
        hours (int, optional): Number of hours to add to the current time when
            setting the run date
        minutes (int, optional): Number of minutes to add to the current time
            when setting the run date

    Raises:
        :obj:`dashboard.exceptions.SchedulerException`: If the job cannot be
            added to the server.

    Returns:
        :obj:`str`: The HTTP reply sent by the server
    """

    scheduled_time = datetime.now()
    if days:
        scheduled_time = scheduled_time + timedelta(days=days)
    if hours:
        scheduled_time = scheduled_time + timedelta(hours=hours)
    if minutes:
        scheduled_time = scheduled_time + timedelta(minutes=minutes)

    extra_args = {
        'trigger': 'date',
        'run_date': scheduled_time,
        'args': input_args
    }
    if input_kwargs:
        extra_args['kwargs'] = input_kwargs

    if not job_id:
        job_id = uuid4().hex

    return scheduler.add_job(job_id, check_function, **extra_args)


def get_emails(users):
    """Retrieve a list of emails for the given users (without duplicates).

    Args:
        users (:obj:`list` of :obj:`dashboard.models.User`): A list of users
            to extract email addresses for.

    Returns:
        list: A :obj:`str` email address for each user.
    """
    recipients = []
    for user in users:
        if not user.email:
            logger.error("No email configured for user {} - {}. Cannot enable "
                         "email notification.".format(user.id, user))
            continue
        if user.email in recipients:
            continue
        recipients.append(user.email)
    return recipients


def monitor_redcap_import(name, num, users=None, study=None):
    """Add a scheduled job to run :obj:`check_redcap`.

    This adds a scheduled job that will run :obj:`check_redcap` two days
    after job submission and notify either the given list of users or staff
    contacts and RAs if a redcap record is not found at that time.

    Args:
        name (:obj:`str`): A session name
        num (int): A session number
        users (:obj:`list` of :obj:`dashboard.models.User`, optional):
            A list of users to notify
        study (:obj:`dashboard.models.Study`, optional): The study to monitor
            if the session exists in more than one.

    Raises:
        :obj:`dashboard.exceptions.MonitorException`: If the 'users' argument
            was not set and no users are set as a staff contact or RA for the
            session's study
        :obj:`dashboard.exceptions.SchedulerException`: If the job cannot
            be added to the server
    """
    session = Session.query.get((name, num))

    if not session.timepoint.expects_redcap() or session.redcap_record:
        return

    db_study = session.get_study(study_id=study)

    if not users:
        users = db_study.get_staff_contacts()
        site = session.timepoint.site.name
        users.extend(db_study.get_RAs(site=site))
        if not users:
            raise MonitorException("No users found to receive redcap import "
                                   "notifications for {}".format(session))

    if not isinstance(users, list):
        users = [users]

    recipients = get_emails(users)
    if not recipients:
        raise MonitorException("None of the expected users {} have an email "
                               "address configured. Cannot send redcap import "
                               "notifications for {}".format(users, session))

    args = [session.name, session.num]
    kwargs = {'recipients': recipients}
    add_monitor(check_redcap, args, input_kwargs=kwargs, days=2)


def check_redcap(name, num, recipients=None):
    """Emails a notification if the given session doesnt have a redcap record.

    Args:
        name (:obj:`str`): A session name
        num (int): A session number
        recipients (:obj:`list` of :obj:`str`, optional): A list of email
            address to notify.

    Raises:
        :obj:`dashboard.exceptions.MonitorException`: If a matching session
            can't be found.
    """
    session = Session.query.get((name, num))
    if not session:
        raise MonitorException("Monitored session {}_{:02d} is no longer in "
                               "database. Cannot verify whether redcap record "
                               "was received.".format(name, num))

    if session.redcap_record:
        return

    missing_redcap_email(str(session),
                         session.get_study().id,
                         dest_emails=recipients)
