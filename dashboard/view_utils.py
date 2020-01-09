#!/usr/bin/env python
"""
Helper functions for the routes defined in views.py to make them a bit more
readable :)
"""
import logging
from functools import wraps

from urllib.parse import urlparse, urljoin
from flask_login import current_user
from flask import flash, url_for, request, redirect
from werkzeug.routing import RequestRedirect

from .models import Study, Timepoint, Scan, RedcapRecord, User
from .utils import create_issue as make_issue

logger = logging.getLogger(__name__)


def report_form_errors(form):
    for field_name, errors in form.errors.items():
        try:
            label = getattr(form, field_name).label.text
        except AttributeError:
            logger.error("Form {} reported an error for a field, but "
                         "field was not found. field_name: {} error(s): "
                         "{}".format(form, field_name, errors))
            continue
        for error in errors:
            flash('ERROR - {} {}'.format(label, error))


def handle_issue(token, issue_form, study_id, timepoint):
    title = clean_issue_title(issue_form.title.data, timepoint)
    study = Study.query.get(study_id)

    staff_member = study.choose_staff_contact()
    if staff_member:
        assigned_user = staff_member.username
    else:
        assigned_user = None

    try:
        issue = make_issue(token, title, issue_form.body.data,
                           assign=assigned_user)
    except Exception as e:
        logger.error("Failed to create a GitHub issue for {}. "
                     "Reason: {}".format(timepoint, e))
        flash("Failed to create issue '{}'".format(title))
    else:
        flash("Issue '{}' created!".format(title))


def clean_issue_title(title, timepoint):
    title = title.rstrip()
    if not title:
        title = timepoint
    elif title.endswith('-'):
        title = title[:-1].rstrip()
    elif timepoint not in title:
        title = timepoint + " - " + title
    return title


def get_timepoint(study_id, timepoint_id, current_user):
    timepoint = Timepoint.query.get(timepoint_id)

    if timepoint is None:
        flash("Timepoint {} does not exist".format(timepoint_id))
        raise RequestRedirect(url_for("main.index"))

    if (not current_user.has_study_access(study_id, timepoint.site_id) or
            not timepoint.belongs_to(study_id)):
        flash("Not authorised to view {}".format(timepoint_id))
        raise RequestRedirect(url_for("main.index"))

    return timepoint


def get_session(timepoint, session_num, fail_url):
    try:
        session = timepoint.sessions[session_num]
    except KeyError:
        flash("Session {} does not exist for {}.".format(session_num,
                                                         timepoint))
        raise RequestRedirect(fail_url)
    return session


def get_scan(scan_id, study_id, current_user, fail_url=None):
    if not fail_url:
        fail_url = url_for('main.index')

    scan = Scan.query.get(scan_id)

    if scan is None:
        logger.error("User {} attempted to retrieve scan with ID {}. "
                     "Retrieval failed.".format(current_user, scan_id))
        flash("Scan does not exist.".format(scan_id))
        raise RequestRedirect(fail_url)

    timepoint = scan.session.timepoint
    if (not current_user.has_study_access(study_id, timepoint.site_id) or
            not timepoint.belongs_to(study_id)):
        flash("Not authorized to view {}".format(scan.name))
        raise RequestRedirect(fail_url)

    return scan


def get_redcap_record(record_id, fail_url=None):
    if not fail_url:
        fail_url = url_for('main.index')

    record = RedcapRecord.query.get(record_id)

    if record is None:
        logger.error("Tried and failed to retrieve RedcapRecord with "
                     "ID {}".format(record_id))
        flash("Record not found.")
        raise RequestRedirect(fail_url)

    return record


def dashboard_admin_required(f):
    """
    Verifies a user is a dashboard admin before granting access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.dashboard_admin:
            flash("Not authorized")
            return redirect(prev_url())
        return f(*args, **kwargs)

    return decorated_function


def study_admin_required(f):
    """
    Verifies a user is a study admin or a dashboard admin. Any view function
    this wraps must have 'study_id' as an argument
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_study_admin(kwargs['study_id']):
            flash("Not authorized.")
            return redirect(prev_url())
        return f(*args, **kwargs)

    return decorated_function


def prev_url():
    """
    Returns the referring page if it is safe to do so, otherwise directs
    the user to the index.
    """
    if request.referrer and is_safe_url(request.referrer):
        return request.referrer
    return url_for('main.index')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')
            and ref_url.netloc == test_url.netloc)
