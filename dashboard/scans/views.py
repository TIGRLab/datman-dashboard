import os
import logging

from flask import render_template, flash, url_for, redirect, send_file
from flask_login import current_user, login_required

from . import utils
from . import scan_bp
from .forms import ScanChecklistForm, SliceTimingForm
from ..view_utils import report_form_errors, get_scan, prev_url

logger = logging.getLogger(__name__)


@scan_bp.route('/', methods=['GET', 'POST'])
@login_required
def scan(study_id, scan_id):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('main.study', study_id=study_id))
    checklist_form = ScanChecklistForm(obj=scan.get_checklist_entry())
    slice_timing_form = SliceTimingForm()
    return render_template('scan.html',
                           scan=scan,
                           study_id=study_id,
                           checklist_form=checklist_form,
                           slice_timing_form=slice_timing_form)


@scan_bp.route('/papaya', methods=['GET'])
@login_required
def papaya(study_id, scan_id):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('main.study', study_id=study_id))
    name = os.path.basename(utils.get_nifti_path(scan))
    return render_template('viewer.html',
                           study_id=study_id,
                           scan_id=scan_id,
                           nifti_name=name)


@scan_bp.route('/slice-timing', methods=['POST'])
@scan_bp.route('/slice-timing/auto/<auto>', methods=['GET'])
@scan_bp.route('/slice-timing/delete/<delete>')
@login_required
def fix_slice_timing(study_id, scan_id, auto=False, delete=False):
    dest_url = url_for('scans.scan', study_id=study_id, scan_id=scan_id)

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


@scan_bp.route('/review', methods=['GET', 'POST'])
@scan_bp.route('/review/<sign_off>', methods=['GET', 'POST'])
@scan_bp.route('/delete/<delete>', methods=['GET', 'POST'])
@scan_bp.route('/update/<update>', methods=['GET', 'POST'])
@login_required
def scan_review(study_id, scan_id, sign_off=False, delete=False, update=False):
    scan = get_scan(scan_id,
                    study_id,
                    current_user,
                    fail_url=url_for('main.study', study_id=study_id))
    dest_url = url_for('scans.scan', study_id=study_id, scan_id=scan_id)

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
    return redirect(url_for('scans.scan', study_id=study_id, scan_id=scan_id))


@scan_bp.route('/load_scan/<string:file_name>')
@login_required
def load_scan(study_id, scan_id, file_name):
    """Sends a scan in a format the papaya viewer can read

    This locates the filesystem path for a scan database record and returns
    it in a format that papaya can work with.

    NOTE: The file name with the correct extension must be the last part of
    the URL or papaya will trip over decompression issues.
    """
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
