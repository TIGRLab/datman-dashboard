from __future__ import absolute_import

import re
import logging

import redcap as REDCAP

import datman.scanid

from config import REDCAP_TOKEN
from .models import RedcapRecord, Session
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
    try:
        new_record = session.add_redcap(record, project, url, instrument, date,
                redcap_user, comment, version)
    except Exception as e:
        raise RedcapException("Failed adding record {} from project {} on "
                "server {}. Reason: {}".format(record, project, url, e))

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

def find_study(ident):
    study = get_study(ident.study, site=ident.site)
    if not study:
        raise RedcapException("Invalid study/site combination: {} {}"
            "".format(ident.study, ident.site))
    return study

def get_timepoint(ident):
    timepoint = Timepoint.query.get(ident.get_full_subjectid_with_timepoint())
    if not timepoint:
        study = find_study(ident)
        timepoint = study.add_timepoint(ident)
    return timepoint
