#!/usr/bin/env python
"""
This script contains a collection of functions that can be given to
the scheduler to help monitor + respond to data errors (for example, checking
if data has been received after a certain interval and emailing someone if not)

The general structure for each monitor is:
    1) A 'monitor' function that gathers input, schedule time, etc. and then
       adds a job to the scheduler
    2) A 'check' function that is what actually runs when the scheduler
       executes the job. This function does the actual work of deciding if
       an email notification needs to be sent at the time of execution
"""
import logging
from uuid import uuid4
from datetime import datetime, timedelta

from dashboard import scheduler, ADMINS
from .models import Session, User, Study
from .emails import missing_session_data_email, missing_redcap_email

logger = logging.getLogger(__name__)

class MonitorException(Exception):
    pass

def add_monitor(check_function, input_args, input_kwargs=None, job_id=None,
        days=None, hours=None, minutes=None):

    scheduled_time = datetime.now()
    if days:
        scheduled_time = scheduled_time + timedelta(days=days)
    if hours:
        scheduled_time = scheduled_time + timedelta(hours=hours)
    if minutes:
        scheduled_time = scheduled_time + timedelta(minutes=minutes)

    extra_args = {'trigger': 'date', 'run_date': scheduled_time,
            'args': input_args}
    if input_kwargs:
        extra_args['kwargs'] = input_kwargs

    if not job_id:
        job_id = uuid4().hex

    return scheduler.add_job(job_id, check_function, **extra_args)

def get_emails(users):
    """
    Reads a list of dashboard.models.User instances and returns a list of emails
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

def monitor_scan_import(session, users=None):
    if not isinstance(session, Session):
        raise MonitorException("Must provide an instance of "
                "dashboard.models.Session to add a scan import monitor. "
                "Received type {}".format(type(session)))

    if not session.missing_scans():
        return

    if not users:
        users = User.query.filter(User.dashboard_admin == True).all()
        if not users:
            raise MonitorException("No users given and no dashboard admins "
                    "found, cant add scan import monitor for {}".format(session))

    if not isinstance(users, list):
        users = [users]

    recipients = get_emails(users)
    if not recipients:
        raise MonitorException("None of the users {} expected to receive scan "
                "import notifications for {} have an email address "
                "configured.".format(users, session))

    args = [session.name, session.num]
    kwargs = {'recipients': recipients}

    add_monitor(check_scans, args, input_kwargs=kwargs, days=2)

def check_scans(name, num, recipients=None):
    session = Session.query.get((name, num))
    if not session:
        raise MonitorException("Monitored session {}_{:02d} is no "
                "longer in database. Cannot verify whether scan data was "
                "received".format(name, num))
    if session.scans:
        return
    missing_session_data_email(str(session), dest_emails=None)

def monitor_redcap_import(name, num, users=None, study=None):
    session = Session.query.get((name, num))

    if not session.timepoint.expects_redcap() or session.redcap_record:
        return

    db_study = session.get_study(study_id=study)

    if not users:
        users = db_study.get_staff_contacts()
        users.extend(db_study.get_RAs())
        if not users:
            raise MonitorException("No users found to receive redcap import "
                    "notifications for {}".format(session))

    if not isinstance(users, list):
        users = [users]

    recipients = get_emails(users)
    if not recipients:
        raise MonitorException("None of the expected users {} have an email "
                "address configured. Cannot send redcap import notifications "
                "for {}".format(users, session))

    args = [session.name, session.num]
    kwargs = {'recipients': recipients}
    add_monitor(check_redcap, args, input_kwargs=kwargs, days=2)

def check_redcap(name, num, recipients=None):
    """
    Recipients should be a list of email addresses.
    """
    session = Session.query.get((name, num))
    if not session:
        raise MonitorException("Monitored session {}_{:02d} is no longer in "
                "database. Cannot verify whether redcap record was "
                "received.".format(name, num))

    if session.redcap_record:
        return

    missing_redcap_email(str(session), session.get_study().id,
            dest_emails=recipients)
