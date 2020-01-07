import json
import csv
import io
import os
import logging

from urllib.parse import urlparse, urljoin
from flask import session as flask_session
from flask import (render_template, flash, url_for, redirect, request, jsonify,
                   make_response, send_file, send_from_directory)
from flask_login import (login_user, logout_user, current_user, login_required,
                         fresh_login_required, login_fresh)

from dashboard import app, db, lm
from . import utils
from . import redcap as REDCAP
from .oauth import OAuthSignIn
from .queries import (query_metric_values_byid, query_metric_types,
                      query_metric_values_byname, find_subjects, find_sessions,
                      find_scans)
from .models import Study, Site, User, Timepoint, Analysis, AccountRequest
from .forms import (SelectMetricsForm, StudyOverviewForm, ScanChecklistForm,
                    UserForm, AnalysisForm, EmptySessionForm,
                    IncidentalFindingsForm, TimepointCommentsForm,
                    NewIssueForm, SliceTimingForm, DataDeletionForm)
from .view_utils import (get_user_form, parse_enabled_sites,
                         report_form_errors, get_timepoint, get_session,
                         get_scan, handle_issue, get_redcap_record,
                         dashboard_admin_required, study_admin_required,
                         prev_url, is_safe_url)
from .emails import incidental_finding_email
from .exceptions import InvalidUsage

logger = logging.getLogger(__name__)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/')
@app.route('/index')
@login_required
def index():
    """
    Main landing page
    """
    studies = current_user.get_studies()

    timepoint_count = Timepoint.query.count()
    study_count = Study.query.count()
    site_count = Site.query.count()
    return render_template('index.html',
                           studies=studies,
                           timepoint_count=timepoint_count,
                           study_count=study_count,
                           site_count=site_count)


@app.route('/search_data')
@app.route('/search_data/<string:search_string>', methods=['GET', 'POST'])
@login_required
def search_data(search_string=None):
    """
    Implements the site's search bar.
    """
    if not search_string:
        # We need the URL endpoint without a search string to enable the use of
        # 'url_for' in the javascript for the 'search' button, but no one
        # should ever actually access the page this way
        flash('Please enter a search term.')
        return redirect('index')

    subjects = find_subjects(search_string)
    if len(subjects) == 1:
        study = subjects[0].accessible_study(current_user)
        if study:
            return redirect(
                url_for('timepoint',
                        study_id=study.id,
                        timepoint_id=subjects[0].name))
    subjects = [
        url_for('timepoint',
                study_id=sub.accessible_study(current_user),
                timepoint_id=sub.name) for sub in subjects
        if sub.accessible_study(current_user)
    ]

    sessions = find_sessions(search_string)
    if len(sessions) == 1:
        study = sessions[0].timepoint.accessible_study(current_user)
        if study:
            return redirect(
                url_for('timepoint',
                        study_id=study.id,
                        timepoint_id=sessions[0].timepoint.name,
                        _anchor="sess" + str(sessions[0].num)))

    sessions = [
        url_for('timepoint',
                study_id=sess.timepoint.accessible_study(current_user),
                timepoint_id=sess.timepoint.name,
                _anchor="sess" + str(sess.num)) for sess in sessions
        if sess.timepoint.accessible_study(current_user)
    ]

    scans = find_scans(search_string)
    if len(scans) == 1:
        study = scans[0].session.timepoint.accessible_study(current_user)
        if study:
            return redirect(
                url_for('scan', study_id=study.id, scan_id=scans[0].id))

    scans = [
        url_for('scan',
                study_id=scan.session.timepoint.accessible_study(current_user),
                scan_id=scan.id) for scan in scans
        if scan.session.timepoint.accessible_study(current_user)
    ]

    return render_template('search_results.html',
                           user_search=search_string,
                           subjects=subjects,
                           sessions=sessions,
                           scans=scans)


# Timepoint view functions ####################################################
# timepoint() is the main view and renders the html users interact with.
#
# The other routes all handle different functionality for the timepoint() view
# and then immediately redirect back to it.


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>',
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
    return render_template('timepoint/main.html',
                           study_id=study_id,
                           timepoint=timepoint,
                           empty_session_form=empty_form,
                           incidental_findings_form=findings_form,
                           timepoint_comments_form=comments_form,
                           issues=github_issues,
                           issue_form=new_issue_form,
                           delete_form=delete_form)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/sign_off/<int:session_num>',
           methods=['GET', 'POST'])
@login_required
def sign_off(study_id, timepoint_id, session_num):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    session = get_session(timepoint, session_num, dest_URL)
    session.sign_off(current_user.id)
    # This is temporary until I add some final touches to sign off process
    for scan in session.scans:
        if scan.is_new():
            scan.add_checklist_entry(current_user.id, sign_off=True)
    return redirect(dest_URL)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/add_comment',
           methods=['POST'])
@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/add_comment/<int:comment_id>',
           methods=['POST', 'GET'])
@login_required
def add_comment(study_id, timepoint_id, comment_id=None):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
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


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/delete_comment/<int:comment_id>',
           methods=['GET'])
@dashboard_admin_required
@login_required
def delete_comment(study_id, timepoint_id, comment_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    try:
        timepoint.delete_comment(comment_id)
    except Exception as e:
        flash("Failed to delete comment. {}".format(e))
    return redirect(dest_URL)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/flag_finding',
           methods=['POST'])
@login_required
def flag_finding(study_id, timepoint_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)

    form = IncidentalFindingsForm()
    if form.validate_on_submit():
        timepoint.report_incidental_finding(current_user.id, form.comment.data)
        incidental_finding_email(current_user, timepoint.name,
                                 form.comment.data)
        flash("Report submitted.")
    return redirect(dest_URL)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/delete',
           methods=['POST'])
@study_admin_required
@login_required
def delete_timepoint(study_id, timepoint_id):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)

    form = DataDeletionForm()
    if not form.validate_on_submit():
        flash("Deletion failed. Please contact an administrator")
        return redirect(
            url_for('timepoint', study_id=study_id, timepoint_id=timepoint_id))

    if form.raw_data.data:
        utils.delete_timepoint(timepoint)

    if form.database_records.data:
        timepoint.delete()

    flash("{} has been deleted.".format(timepoint))
    return redirect(url_for('study', study_id=study_id))


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/delete_session/<int:session_num>',
           methods=['POST'])
@study_admin_required
@login_required
def delete_session(study_id, timepoint_id, session_num):
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
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
@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>'
           '/delete_scan/',
           methods=['POST'])
@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>'
           '/delete_scan/<int:scan_id>',
           methods=['POST'])
@study_admin_required
@login_required
def delete_scan(study_id, timepoint_id, scan_id):
    dest_URL = url_for('timepoint',
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


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/dismiss_redcap/<int:session_num>',
           methods=['GET', 'POST'])
@study_admin_required
@login_required
def dismiss_redcap(study_id, timepoint_id, session_num):
    """
    Dismiss a session's 'missing redcap' error message.
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    get_session(timepoint, session_num, dest_URL)
    timepoint.dismiss_redcap_error(session_num)
    flash("Successfully updated.")
    return redirect(dest_URL)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/dismiss_missing/<int:session_num>',
           methods=['POST'])
@study_admin_required
@login_required
def dismiss_missing(study_id, timepoint_id, session_num):
    """
    Dismiss a session's 'missing scans' error message
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)
    get_session(timepoint, session_num, dest_URL)

    form = EmptySessionForm()
    if form.validate_on_submit():
        timepoint.ignore_missing_scans(session_num, current_user.id,
                                       form.comment.data)
        flash("Succesfully updated.")

    return redirect(dest_URL)


@app.route('/study/<string:study_id>/timepoint/<string:timepoint_id>' +
           '/create_issue',
           methods=['POST'])
@login_required
def create_issue(study_id, timepoint_id):
    """
    Posts a new issue to Github
    """
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    dest_URL = url_for('timepoint',
                       study_id=study_id,
                       timepoint_id=timepoint_id)

    form = NewIssueForm()
    if not form.validate_on_submit():
        report_form_errors(form)
        return redirect(dest_URL)
    token = flask_session['active_token']

    handle_issue(token, form, study_id, timepoint.name)

    return redirect(dest_URL)


# End of Timepoint View functions ############################################


@app.route('/redcap', methods=['GET', 'POST'])
def redcap():
    """
    A redcap server can send a notification to this URL when a survey is saved
    and the record will be retrieved from the redcap server and saved to the
    database.
    """
    logger.info('Received a query from redcap')
    if request.method != 'POST':
        logger.error('Received an invalid redcap request. A REDCAP data '
                     'callback may be misconfigured')
        raise InvalidUsage('Expected a POST request', status_code=400)

    logger.debug('Received keys {} from REDcap from URL {}'.format(
        list(request.form.keys()), request.form['project_url']))
    try:
        REDCAP.create_from_request(request)
    except Exception as e:
        logger.error('Failed creating redcap object. Reason: {}'.format(e))
        raise InvalidUsage(str(e), status_code=400)

    return render_template('200.html'), 200


@app.route('/redcap_redirect/<int:record_id>', methods=['GET'])
@login_required
def redcap_redirect(record_id):
    """
    Used to provide a link from the session page to a redcap session complete
    record on the redcap server itself.
    """
    record = get_redcap_record(record_id)

    if record.event_id:
        event_string = "&event_id={}".format(record.event_id)
    else:
        event_string = ""

    redcap_url = '{}redcap_v{}/DataEntry/index.php?pid={}&id={}{}&page={}'
    redcap_url = redcap_url.format(record.url, record.redcap_version,
                                   record.project, record.record, event_string,
                                   record.instrument)

    return redirect(redcap_url)


@app.route('/study/<string:study_id>/scan/<int:scan_id>',
           methods=['GET', 'POST'])
@login_required
def scan(study_id, scan_id):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('study', study_id=study_id))
    checklist_form = ScanChecklistForm(obj=scan.get_checklist_entry())
    slice_timing_form = SliceTimingForm()
    return render_template('scan/main.html',
                           scan=scan,
                           study_id=study_id,
                           checklist_form=checklist_form,
                           slice_timing_form=slice_timing_form)


@app.route('/study/<string:study_id>/papaya/<int:scan_id>', methods=['GET'])
@login_required
def papaya(study_id, scan_id):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('study', study_id=study_id))
    name = os.path.basename(utils.get_nifti_path(scan))
    return render_template('scan/viewer.html',
                           study_id=study_id,
                           scan_id=scan_id,
                           nifti_name=name)


@app.route('/study/<string:study_id>/slice-timing/<int:scan_id>',
           methods=['POST'])
@app.route('/study/<string:study_id>/slice-timing/<int:scan_id>/auto/<auto>',
           methods=['GET'])
@app.route('/study/<string:study_id>/slice-timing/<int:scan_id>'
           '/delete/<delete>')
@login_required
def fix_slice_timing(study_id, scan_id, auto=False, delete=False):
    dest_url = url_for('scan', study_id=study_id, scan_id=scan_id)

    scan = get_scan(scan_id, study_id, current_user)
    # Need a new dictionary to get the changes to actually save
    new_json = dict(scan.json_contents)

    if auto:
        new_json["SliceTiming"] = scan.get_header_diffs(
        )["SliceTiming"]["expected"]
    elif delete:
        del new_json["SliceTiming"]
    else:
        timing_form = SliceTimingForm()
        if not timing_form.validate_on_submit():
            flash("Failed to update slice timings")
            return redirect(dest_url)

        new_timings = timing_form.timings.data
        new_timings = new_timings.replace("[", "").replace("]", "")
        new_json["SliceTiming"] = [
            float(item.strip()) for item in new_timings.split(",")
        ]

    try:
        utils.update_json(scan, new_json)
    except Exception as e:
        logger.error("Failed updating slice timings for scan {}. Reason {} "
                     "{}".format(scan_id,
                                 type(e).__name__, e))
        flash("Failed during slice timing update. Please contact an admin for "
              "help")
        return redirect(dest_url)

    utils.update_header_diffs(scan)
    flash("Update successful")

    return redirect(dest_url)


@app.route('/study/<string:study_id>/scan/<int:scan_id>/review',
           methods=['GET', 'POST'])
@app.route('/study/<string:study_id>/scan/<int:scan_id>/review/<sign_off>',
           methods=['GET', 'POST'])
@app.route('/study/<string:study_id>/scan/<int:scan_id>/delete/<delete>',
           methods=['GET', 'POST'])
@app.route('/study/<string:study_id>/scan/<int:scan_id>/update/<update>',
           methods=['GET', 'POST'])
@login_required
def scan_review(study_id, scan_id, sign_off=False, delete=False, update=False):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('study', study_id=study_id))
    dest_url = url_for('scan', study_id=study_id, scan_id=scan_id)

    if delete:
        entry = scan.get_checklist_entry()
        entry.delete()
        return redirect(dest_url)

    if sign_off:
        # Just in case the value provided in the URL was not boolean
        sign_off = True

    checklist_form = ScanChecklistForm()
    if checklist_form.is_submitted():
        if not checklist_form.validate_on_submit():
            report_form_errors(checklist_form)
            return redirect(dest_url)
        comment = checklist_form.comment.data
    else:
        comment = None

    if update:
        # Update is done separately so that a review entry can't accidentally
        # be changed from 'flagged' to blacklisted.
        if comment is None:
            flash("Cannot update entry with empty comment")
            return redirect(dest_url)
        scan.add_checklist_entry(current_user.id, comment)
        return redirect(dest_url)

    scan.add_checklist_entry(current_user.id, comment, sign_off)
    return redirect(url_for('scan', study_id=study_id, scan_id=scan_id))


@app.route('/study/<string:study_id>', methods=['GET', 'POST'])
@app.route('/study/<string:study_id>/<active_tab>', methods=['GET', 'POST'])
@login_required
def study(study_id=None, active_tab=None):
    """
    This is the main view for a single study.
    The page is a tabulated view, I would have done this differently given
    another chance.
    """
    if not current_user.has_study_access(study_id):
        flash('Not authorised')
        return redirect(url_for('index'))

    # get the list of metrics for to graph from the study config
    display_metrics = app.config['DISPLAY_METRICS']

    # get the study object from the database
    study = Study.query.get(study_id)

    # this is used to update the readme text file
    form = StudyOverviewForm()

    if form.validate_on_submit():
        # form has been submitted check for changes
        # simple MD seems to replace \n with \r\n
        form.readme_txt.data = form.readme_txt.data.replace('\r', '')

        # also strip blank lines at the start and end as these are
        # automatically stripped when the form is submitted
        if not form.readme_txt.data.strip() == study.read_me:
            study.read_me = form.readme_txt.data
            study.save()

    form.readme_txt.data = study.read_me
    form.study_id.data = study_id

    return render_template('study.html',
                           metricnames=study.get_valid_metric_names(),
                           study=study,
                           form=form,
                           active_tab=active_tab,
                           display_metrics=display_metrics)


@app.route('/person')
@app.route('/person/<int:person_id>', methods=['GET'])
@login_required
def person(person_id=None):
    """
    Place holder, does nothing
    """
    return redirect('/index')


@app.route('/metricData', methods=['GET', 'POST'])
@login_required
def metricData():
    """
    This is a generic view for querying the database and allows selection of
    any combination of metrics and returns the data.

    The form is submitted on any change, this allows dynamic updating of the
    selection boxes displayed in the html (i.e. if SPINS study is selected
    the sites selector is filtered to only show sites relevent to SPINS).

    We only actually query and return the data if the query_complete is defined
    as true - this is done by client-side javascript.

    A lot of this could have been done client side but I think we all prefer
    writing python to javascript.
    """
    form = SelectMetricsForm()
    data = None
    csv_data = None
    csvname = 'dashboard/output.csv'
    w_file = open(csvname, 'w')

    if form.query_complete.data == 'True':
        data = metricDataAsJson()
        # convert the json object to csv format
        # Need the data field of the response object (data.data)
        temp_data = json.loads(data.data)["data"]
        if temp_data:

            testwrite = csv.writer(w_file)

            csv_data = io.BytesIO()
            csvwriter = csv.writer(csv_data)
            csvwriter.writerow(list(temp_data[0].keys()))
            testwrite.writerow(list(temp_data[0].keys()))
            for row in temp_data:
                csvwriter.writerow(list(row.values()))
                testwrite.writerow(list(row.values()))

    w_file.close()

    # anything below here is for making the form boxes dynamic
    if any([
            form.study_id.data, form.site_id.data, form.scantype_id.data,
            form.metrictype_id.data
    ]):
        form_vals = query_metric_types(studies=form.study_id.data,
                                       sites=form.site_id.data,
                                       scantypes=form.scantype_id.data,
                                       metrictypes=form.metrictype_id.data)

    else:
        form_vals = query_metric_types()

    study_vals = []
    site_vals = []
    scantype_vals = []
    metrictype_vals = []

    for res in form_vals:
        study_vals.append((res[0].id, res[0].name))
        site_vals.append((res[1].name, res[1].name))
        scantype_vals.append((res[2].tag, res[2].tag))
        metrictype_vals.append((res[3].id, res[3].name))
        # study_vals.append((res.id, res.name))
        # for site in res.sites:
        #     site_vals.append((site.id, site.name))
        # for scantype in res.scantypes:
        #     scantype_vals.append((scantype.id, scantype.name))
        #     for metrictype in scantype.metrictypes:
        #         metrictype_vals.append((metrictype.id, metrictype.name))

    # sort the values alphabetically
    study_vals = sorted(set(study_vals), key=lambda v: v[1])
    site_vals = sorted(set(site_vals), key=lambda v: v[1])
    scantype_vals = sorted(set(scantype_vals), key=lambda v: v[1])
    metrictype_vals = sorted(set(metrictype_vals), key=lambda v: v[1])

    flask_session['study_name'] = study_vals
    flask_session['site_name'] = site_vals
    flask_session['scantypes_name'] = scantype_vals
    flask_session['metrictypes_name'] = metrictype_vals

    # this bit actually updates the valid selections on the form
    form.study_id.choices = study_vals
    form.site_id.choices = site_vals
    form.scantype_id.choices = scantype_vals
    form.metrictype_id.choices = metrictype_vals

    reader = csv.reader(open(csvname, 'r'))
    csvList = [row for row in reader]

    if csv_data:
        csv_data.seek(0)
        return render_template('getMetricData.html', form=form, data=csvList)
    else:
        return render_template('getMetricData.html', form=form, data="")


def _checkRequest(request, key):
    # Checks a post request, returns none if key doesn't exist
    try:
        return (request.form.getlist(key))
    except KeyError:
        return (None)


@app.route('/DownloadCSV')
@login_required
def downloadCSV():

    output = make_response(send_file('output.csv', as_attachment=True))
    output.headers["Content-Disposition"] = "attachment; filename=output.csv"
    output.headers["Content-type"] = "text/csv"
    output.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    output.headers['Pragma'] = 'no-cache'
    return output


@app.route('/metricDataAsJson', methods=['Get', 'Post'])
@login_required
def metricDataAsJson(format='http'):
    """
    Query the database for metrics. Handles both GET (generated by client side
    javascript for creating graphs) and POST (generated by the metricData
    form view) requests

    Can be accessed at:
       http://srv-dashboard.camhres.ca/metricDataAsJson

    This will return all data in the database (probs not what you want).

    Filters can be defined in the http request object
    (http://flask.pocoo.org/docs/0.12/api/#incoming-request-data)
    this is a global flask object that is automatically created whenever a URL
    is requested. e.g.:

    <url>/metricDataAsJson?studies=15&sessions=1739,1744&metrictypes=84
    creates a request object
            request.args = {studies: 15,
                            sessions: [1739, 1744],
                            metrictypes: 84}
    If byname is defined (and evaluates True) in the request.args then filters
    can be defined by name instead of by database id e.g.
    <url>/metricDataAsJson?byname=True&studies=ANDT&sessions=ANDT_CMH_101_01

    Function works slightly differently if the request method is POST
    (such as that generated by metricData()). In that case the field names are
    expected to be the primary keys from the database as these are used to
    create the form.
    """
    # Define the mapping from GET field names to POST field names
    # it's going to get replaced either by the requested values (if defined in
    # the request object) or by None if not set as a filter
    fields = {
        'studies': 'study_id',
        'sites': 'site_id',
        'sessions': 'session_id',
        'scans': 'scan_id',
        'scantypes': 'scantype_id',
        'metrictypes': 'metrictype_id'
    }

    byname = False  # switcher to allow getting values byname instead of id

    try:
        if request.method == 'POST':
            byname = request.form['byname']
        else:
            byname = request.args.get('byname')
    except KeyError:
        pass

    # extract the values from the request object and populate
    for k, v in fields.items():
        if request.method == 'POST':
            fields[k] = _checkRequest(request, v)
        else:
            if request.args.get(k):
                fields[k] = [x.strip() for x in request.args.get(k).split(',')]
            else:
                fields[k] = None

    # remove None values from the dict
    fields = dict((k, v) for k, v in fields.items() if v)

    # make the database query
    if byname:
        data = query_metric_values_byname(**fields)
    else:
        # convert from strings to integers
        for k, vals in fields.items():
            try:
                fields[k] = int(vals)
            except TypeError:
                fields[k] = [int(v) for v in vals]

        data = query_metric_values_byid(**fields)

    # the database query returned a list of sqlachemy record objects.
    # convert these into a standard list of dicts so we can jsonify it
    objects = []

    for metricValue in data:
        session = [
            session_link.session for session_link in metricValue.scan.sessions
            if session_link.is_primary
        ][0]
        objects.append({
            'value': metricValue.value,
            'metrictype': metricValue.metrictype.name,
            'metrictype_id': metricValue.metrictype_id,
            'scan_id': metricValue.scan_id,
            'scan_name': metricValue.scan.name,
            'scan_description': metricValue.scan.description,
            'scantype': metricValue.scan.scantype.name,
            'scantype_id': metricValue.scan.scantype_id,
            'session_id': session.id,
            'session_name': session.name,
            # 'session_date':     metricValue.scan.session.date,
            'site_id': session.site_id,
            'site_name': session.site.name,
            'study_id': session.study_id,
            'study_name': session.study.name
        })

    if format == 'http':
        # spit this out in a format suitable for client side processing
        return (jsonify({'data': objects}))
    else:
        # return a pretty object for human readable
        return (json.dumps(objects, indent=4, separators=(',', ': ')))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/analysis', methods=['GET', 'POST'])
@app.route('/analysis/<analysis_id>')
@login_required
def analysis(analysis_id=None):
    """
    Default view for analysis
    """
    form = AnalysisForm()
    if form.validate_on_submit():
        try:
            analysis = Analysis()
            analysis.name = form.name.data
            analysis.description = form.description.data
            analysis.software = form.software.data

            db.session.add(analysis)
            db.session.commit()
            flash('Analysis added')
        except Exception:
            flash('Failed adding analysis')

    if not analysis_id:
        analyses = Analysis.query.all()
    else:
        analyses = Analysis.query.get(analysis_id)

    for analysis in analyses:
        # format the user objects for display on page
        users = analysis.get_users()
        analysis.user_names = ' '.join([user.realname for user in users])

    return render_template('analyses.html', analyses=analyses, form=form)


# These functions serve up static files from the local filesystem
@app.route('/study/<string:study_id>/data/RESOURCES/<path:tech_notes_path>')
@app.route('/study/<string:study_id>/qc/<string:timepoint_id>/index.html')
@app.route('/study/<string:study_id>/qc/<string:timepoint_id>'
           '/<regex(".*\.png"):image>')  # noqa: W605
@login_required
def static_qc_page(study_id,
                   timepoint_id=None,
                   image=None,
                   tech_notes_path=None):
    if tech_notes_path:
        resources = utils.get_study_path(study_id, 'resources')
        return send_from_directory(resources, tech_notes_path)
    timepoint = get_timepoint(study_id, timepoint_id, current_user)
    if image:
        qc_dir, _ = os.path.split(timepoint.static_page)
        return send_from_directory(qc_dir, image)
    return send_file(timepoint.static_page)


# The file name (with correct extension) needs to be last part of the URL or
# papaya will fail to read the file because it wont figure out on its own
# whether or not a file needs decompression
@app.route('/study/<string:study_id>/load_scan/<int:scan_id>/'
           '<string:file_name>')
@login_required
def load_scan(study_id, scan_id, file_name):
    scan = get_scan(scan_id, study_id, current_user, fail_url=prev_url())
    full_path = utils.get_nifti_path(scan)
    try:
        result = send_file(full_path,
                           as_attachment=True,
                           attachment_filename=file_name,
                           mimetype="application/gzip")
    except IOError as e:
        logger.error("Couldnt find file {} to load scan view for user "
                     "{}".format(full_path, current_user))
        result = not_found_error(e)
    return result
