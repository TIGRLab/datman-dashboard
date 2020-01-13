import logging

from flask import (render_template, redirect, request)
from flask_login import login_required

from . import rcap_bp
import .redcap as REDCAP
from ..view_utils import get_redcap_record
from ..exceptions import InvalidUsage


logger = logging.getLogger(__name__)


@rcap_bp.route('/redcap', methods=['GET', 'POST'])
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


@rcap_bp.route('/redcap_redirect/<int:record_id>', methods=['GET'])
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
