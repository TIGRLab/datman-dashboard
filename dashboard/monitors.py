#!/usr/bin/env python
"""
This script contains a collection of functions that can be given to
the scheduler to help monitor + respond to data errors (for example, checking
if data has been received after a certain interval and emailing someone if not)
"""
from uuid import uuid4
from datetime import datetime, timedelta

from dashboard import scheduler
from .models import Session, RedcapRecord
from .emails import missing_session_data_email, missing_redcap_email

class MonitorException(Exception):
    pass

def monitor_scan_import(session):
    id = uuid4().hex
    scheduled_time = datetime.now() + timedelta(minutes=5)
    extra_args = {'trigger': 'date', 'run_date': scheduled_time,
            'args': [session.name, session.num]}
    scheduler.add_job(id, check_scans, **extra_args)

def check_scans(name, num):
    session = Session.query.get((name, num))
    if not session:
        raise MonitorException("Redcap record had been received without "
                "scan data for {}_{} but no session found in database "
                "at 48 hour follow up.".format(name, num))
    if session.scans:
        return
    missing_session_data_email(str(session))
