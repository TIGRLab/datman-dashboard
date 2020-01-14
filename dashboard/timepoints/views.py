import logging

from flask import session as flask_session
from flask import (current_app, render_template, flash, url_for, redirect)
from flask_login import (current_user, login_required, fresh_login_required)

from . import time_bp
from . import utils
from .forms import (EmptySessionForm, IncidentalFindingsForm,
                    TimepointCommentsForm, NewIssueForm, DataDeletionForm)
from ..view_utils import (report_form_errors, get_timepoint, get_session,
                          get_scan, dashboard_admin_required,
                          study_admin_required)
from ..emails import incidental_finding_email

logger = logging.getLogger(__name__)


@time_bp.route('/',
           methods=['GET', 'POST'])
@fresh_login_required
def timepoint(study_id, timepoint_id):
    """
    Default view for a single timepoint.
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)

    try:
        token = flask_session['active_token']
    except KeyError:
        github_issues = None
    else:
        try:
            github_issues = utils.search_issues(token, timepoint.name)
        except Exception:
            flash("Github issue access failed. Please contact an admin if "
                  "this issue persists.")
            logger.debug("Can't search github issues, user {} received "
                         "access denied.".format(current_user))
            github_issues = None

    empty_form = EmptySessionForm()
    findings_form = IncidentalFindingsForm()
    comments_form = TimepointCommentsForm()
    new_issue_form = NewIssueForm()
    delete_form = DataDeletionForm()
    new_issue_form.title.data = timepoint.name + " - "
    return render_template('main.html',
                           study_id=study_id,
                           timepoint=timepoint,
                           empty_session_form=empty_form,
                           incidental_findings_form=findings_form,
                           timepoint_comments_form=comments_form,
                           issues=github_issues,
                           issue_form=new_issue_form,
                           delete_form=delete_form)


@time_bp.route('/sign_off/<int:session_num>', methods=['GET', 'POST'])
@login_required
def sign_off(study_id, timepoint_id, session_num):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    session = get_session(timepoint, session_num, dest_URL)
    session.sign_off(current_user.id)
    # This is temporary until I add some final touches to sign off process
    for scan in session.scans:
        if scan.is_new():
            scan.add_checklist_entry(current_user.id, sign_off=True)
    return redirect(dest_URL)


@time_bp.route('/add_comment', methods=['POST'])
@time_bp.route('/add_comment/<int:comment_id>', methods=['POST', 'GET'])
@login_required
def add_comment(study_id, timepoint_id, comment_id=None):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)

    form = TimepointCommentsForm()
    if form.validate_on_submit():
        if comment_id:
            try:
                timepoint.update_comment(current_user.id, comment_id,
                                         form.comment.data)
            except Exception as e:
                flash("Failed to update comment. Reason: {}".format(e))
            else:
                flash("Updated comment.")
            return redirect(dest_URL)
        timepoint.add_comment(current_user.id, form.comment.data)
    return redirect(dest_URL)


@time_bp.route('/delete_comment/<int:comment_id>', methods=['GET'])
@dashboard_admin_required
@login_required
def delete_comment(study_id, timepoint_id, comment_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    try:
        timepoint.delete_comment(comment_id)
    except Exception as e:
        flash("Failed to delete comment. {}".format(e))
    return redirect(dest_URL)


@time_bp.route('/flag_finding', methods=['POST'])
@login_required
def flag_finding(study_id, timepoint_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)

    form = IncidentalFindingsForm()
    if form.validate_on_submit():
        timepoint.report_incidental_finding(current_user.id, form.comment.data)
        incidental_finding_email(current_user, timepoint.name,
                                 form.comment.data)
        flash("Report submitted.")
    return redirect(dest_URL)


@time_bp.route('/delete', methods=['POST'])
@study_admin_required
@login_required
def delete_timepoint(study_id, timepoint_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)

    form = DataDeletionForm()
    if not form.validate_on_submit():
        flash("Deletion failed. Please contact an administrator")
        return redirect(
            url_for('timepoints.timepoint', study_id=study_id, timepoint_id=timepoint_id))

    if form.raw_data.data:
        utils.delete_timepoint(timepoint)

    if form.database_records.data:
        timepoint.delete()

    flash("{} has been deleted.".format(timepoint))
    return redirect(url_for('main.study', study_id=study_id))


@time_bp.route('/delete_session/<int:session_num>', methods=['POST'])
@study_admin_required
@login_required
def delete_session(study_id, timepoint_id, session_num):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    session = get_session(timepoint, session_num, dest_URL)

    form = DataDeletionForm()
    if not form.validate_on_submit():
        flash("Deletion failed. Please contact an administrator")
        return redirect(dest_URL)

    if form.raw_data.data:
        if len(timepoint.sessions) == 1:
            utils.delete_timepoint(timepoint)
        else:
            utils.delete_session(session)

    if form.database_records.data:
        session.delete()

    flash("{} has been deleted.".format(session))
    return redirect(dest_URL)


# The route without a scanid never actually receives requests but is
# needed for the url_for call to work when scan id wont be known until later
@time_bp.route('/delete_scan/', methods=['POST'])
@time_bp.route('/delete_scan/<int:scan_id>', methods=['POST'])
@study_admin_required
@login_required
def delete_scan(study_id, timepoint_id, scan_id):
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    scan = get_scan(scan_id, study_id, current_user, dest_URL)

    form = DataDeletionForm()
    if not form.validate_on_submit():
        flash("Deletion failed. Please contact an admin")
        return redirect(dest_URL)

    if form.raw_data.data:
        utils.delete_scan(scan)

    if form.database_records.data:
        scan.delete()

    return redirect(dest_URL)


@time_bp.route('/dismiss_redcap/<int:session_num>',
                    methods=['GET', 'POST'])
@study_admin_required
@login_required
def dismiss_redcap(study_id, timepoint_id, session_num):
    """
    Dismiss a session's 'missing redcap' error message.
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    get_session(timepoint, session_num, dest_URL)
    timepoint.dismiss_redcap_error(session_num)
    flash("Successfully updated.")
    return redirect(dest_URL)


@time_bp.route('/dismiss_missing/<int:session_num>', methods=['POST'])
@study_admin_required
@login_required
def dismiss_missing(study_id, timepoint_id, session_num):
    """
    Dismiss a session's 'missing scans' error message
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    get_session(timepoint, session_num, dest_URL)

    form = EmptySessionForm()
    if form.validate_on_submit():
        timepoint.ignore_missing_scans(session_num, current_user.id,
                                       form.comment.data)
        flash("Succesfully updated.")

    return redirect(dest_URL)


@time_bp.route('/create_issue', methods=['POST'])
@login_required
def create_issue(study_id, timepoint_id):
    """
    Posts a new issue to Github
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoints.timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)

    form = NewIssueForm()
    if not form.validate_on_submit():
        report_form_errors(form)
        return redirect(dest_URL)
    token = flask_session['active_token']

    utils.handle_issue(token, form, study_id, timepoint.name)

    return redirect(dest_URL)
