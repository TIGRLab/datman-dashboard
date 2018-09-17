#!/usr/bin/env python
"""
Helper functions for the routes defined in views.py to make them a bit more
readable :)
"""
import logging

from flask import flash
from werkzeug.routing import RequestRedirect

from .models import Study, Timepoint
from .forms import UserForm, UserAdminForm

logger = logging.getLogger(__name__)

def get_user_form(user, current_user):
    if not current_user.dashboard_admin:
        return UserForm(obj=user)

    form = UserAdminForm(obj=user)
    disabled_studies = user.get_disabled_studies()
    form.add_access.choices = [(study.id, study.id) for study in
            disabled_studies]
    return form

def report_form_errors(form):
    for field_name, errors in form.errors.items():
        try:
            label = getattr(form, field_name).label.text
        except:
            logger.error("Form {} reported an error for a field, but "
                "field was not found. field_name: {} error(s): {}".format(
                form, field_name, errors))
            continue
        for error in errors:
            flash('ERROR - {} {}'.format(label, error))

def get_timepoint(study_id, timepoint_id, current_user):
    timepoint = Timepoint.query.get(timepoint_id)

    if timepoint is None:
        flash("Timepoint {} does not exist".format(timepoint_id))
        raise RequestRedirect("index")

    if (not current_user.has_study_access(study_id) or
            not timepoint.belongs_to(study_id)):
        flash("Not authorised to view {}".format(timepoint_id))
        raise RequestRedirect("index")

    return timepoint

def get_session(timepoint, session_num, fail_url):
    try:
        session = timepoint.sessions[session_num]
    except KeyError:
        flash("Session {} does not exist for {}.".format(session_num, timepoint))
        raise RequestRedirect(fail_url)
    return session
