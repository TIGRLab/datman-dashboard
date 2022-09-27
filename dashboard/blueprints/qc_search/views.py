from flask import render_template, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from . import checklist_bp
from .forms import QcSearchForm
from ...models import ExpectedScan, StudyUser
from ...queries import get_scan_qc


@checklist_bp.route('/', methods=["GET"])
@login_required
def qc_search():
    """Get the QC review search form page.
    """

    form = QcSearchForm()
    form.study.choices = [
        (study.id, study.id) for study in current_user.get_studies()
    ]
    form.site.choices = [
        (site, site) for site in current_user.get_sites()
    ]
    form.tag.choices = [
        (tag, tag) for tag, *rest in get_tags(current_user)
    ]

    return render_template('qc_search.html', search_form=form)


@checklist_bp.route('/submit-query', methods=["POST"])
@login_required
def lookup_data():
    """Use AJAX to submit search terms and get a set of QC reviews.
    """
    return {}


def get_tags(user):
    query = ExpectedScan.query.join(
        StudyUser,
        StudyUser.study_id == ExpectedScan.study_id)\
        .filter(StudyUser.user_id == user.id)\
        .filter(
            or_(StudyUser.site_id == None,
                StudyUser.site_id == ExpectedScan.site_id))\
        .with_entities(ExpectedScan.scantype_id)
    return query.all()
