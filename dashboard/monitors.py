#!/usr/bin/env python
"""
This script contains a collection of functions that can be given to
the scheduler to help monitor + respond to data errors (for example, checking
if data has been received after a certain interval and emailing someone if not)
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

def monitor_scan_import(session):
    id = uuid4().hex
    scheduled_time = datetime.now() + timedelta(days=2)
    extra_args = {'trigger': 'date', 'run_date': scheduled_time,
            'args': [session.name, session.num]}
    scheduler.add_job(id, check_scans, **extra_args)

def check_scans(name, num):
    session = Session.query.get((name, num))
    if not session:
        raise MonitorException("Monitored session {}_{:02d} is no "
                "longer in database. Cannot verify whether scan data was "
                "received".format(name, num))
    if session.scans:
        return
    missing_session_data_email(str(session))

def monitor_redcap_import(name, num, study=None):
    if study:
        db_study = Study.query.get(study)
    else:
        session = Session.query.get((name, num))
        db_study = session.timepoint.studies.values()[0]

    contacts = db_study.get_staff_contacts()
    contacts.extend(db_study.get_RAs())
    if not contacts:
        logger.info("No staff contacts or RAs configured for study {}. "
                "Dashboard admins will receive any notifications for missing "
                "redcap surveys instead.".format(db_study))

    recipients = []
    for user in contacts:
        if not user.email:
            logger.error("No contact information configured for user {} with "
                    "ID {}. Can't set up redcap survey notification.".format(
                    user, user.id))
            continue
        recipients.append(user.email)

    # Just in case someone has been added twice
    recipients = list(set(recipients))
    id = uuid4().hex
    scheduled_time = datetime.now() + timedelta(days=2)
    extra_args = {'trigger': 'date', 'run_date': scheduled_time,
            'args': [session.name, session.num],
            'kwargs': {'recipients': recipients}}
    scheduler.add_job(id, check_redcap, **extra_args)

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

    if not recipients:
        recipients = ADMINS
    if not isinstance(recipients, list):
        recipients = [recipients]

    for email in recipients:
        missing_redcap_email(str(session), dest_email=email)
