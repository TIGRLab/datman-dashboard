from __future__ import absolute_import

import re
import logging

import requests
import redcap as REDCAP

import datman.scanid

from config import REDCAP_TOKEN
from .models import RedcapRecord, Session, Study, Site, db
from .queries import get_study

logger = logging.getLogger(__name__)

class RedcapException(Exception):
    """Generic error for recap interface"""

def create_from_request(request):
    try:
        record = request.form['record']
        project = request.form['project_id']
        url = request.form['redcap_url']
        instrument = request.form['instrument']
        version = re.search('redcap_v(.*)\/index',
                request.form['project_url']).group(1)
        completed = int(request.form[instrument + '_complete'])
    except KeyError:
        raise RedcapException('Redcap data entry trigger request missing a '
                'required key. Found keys: {}'.format(request.form.keys()))

    if completed != 2:
        logger.info("Record {} not completed. Ignoring".format(record))
        return

    rc = REDCAP.Project(url + 'api/', REDCAP_TOKEN)
    server_record = rc.export_records([record])

    if len(server_record) < 0:
        raise RedcapException('Record {} not found on redcap server {}'.format(
                record, url))
    elif len(server_record) > 1:
        raise RedcapException('Found {} records matching {} on redcap server '
                '{}'.format(len(server_record), record, url))

    server_record = server_record[0]

    try:
        date = server_record['date']
        comment = server_record['cmts']
        redcap_user = server_record['ra_id']
        session_name = server_record['par_id']
    except KeyError:
        raise RedcapException('Redcap record {} from server {} missing a '
                'required field. Found keys: {}'.format(record,
                server_record.keys()))

    session = set_session(session_name)
    if session.redcap_record:
        orig_record = session.redcap_record.record
        if (orig_record.record != record or
                str(orig_record.project) != project or
                orig_record.url != url):
            raise RedcapException("Redcap record already found for {}. "
                    "Please delete original record before adding a new "
                    "one".format(session))
        orig_record.instrument = instrument
        orig_record.date = date
        orig_record.user = redcap_user
        orig_record.comment = comment
        orig_record.redcap_version = version
        db.session.add(orig_record)
        db.session.commit()
        return orig_record

    new_record = RedcapRecord(record, project, url)
    new_record.instrument = instrument
    new_record.date = date
    new_record.user = redcap_user
    new_record.comment = comment
    new_record.redcap_version = version
    session.add_redcap(new_record)

    return new_record

def set_session(name):
    name = name.upper()
    try:
        ident = datman.scanid.parse(name)
    except datman.scanid.ParseException:
        raise RedcapException("Invalid session ID {}".format(name))

    name = ident.get_full_subjectid_with_timepoint()
    num = datman.scanid.get_session_num(ident)

    session = Session.query.get((name, num))
    if not session:
        timepoint = get_timepoint(ident)
        session = timepoint.add_session(num)
    return session

def get_study(ident):
    study = queries.get_study(ident.study, site=ident.site)
    if not study:
        raise RedcapException("Invalid study/site combination: {} {}"
            "".format(ident.study, ident.site))
    return study

def get_timepoint(ident):
    timepoint = Timepoint.query.get(ident.get_full_subjectid_with_timepoint())
    if not timepoint:
        study = get_study(ident)
        timepoint = study.add_timepoint(ident)
    return timepoint
