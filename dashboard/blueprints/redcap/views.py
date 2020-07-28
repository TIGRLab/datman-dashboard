import logging

from flask import (render_template, redirect, request)
from flask_login import login_required

from . import rcap_bp
from . import utils
from ...exceptions import InvalidUsage

logger = logging.getLogger(__name__)


@rcap_bp.route('/redcap', methods=['POST'])
def redcap():
    """URL endpoint to receive redcap data entry triggers.

    A redcap server can send a notification to this URL when a survey is saved
    and the record will be retrieved and saved to the database.
    """
    logger.debug('Received keys {} from REDcap from URL {}'.format(
        list(request.form.keys()), request.form['project_url']))
    try:
        utils.create_from_request(request)
    except Exception as e:
        logger.error('Failed creating redcap object. Reason: {}'.format(e))
        raise InvalidUsage(str(e), status_code=400)

    return 'Record successfully added', 200


@rcap_bp.route('/redcap_redirect/<int:record_id>', methods=['GET'])
@login_required
def redcap_redirect(record_id):
    """
    Used to provide a link from the session page to a redcap session complete
    record on the redcap server itself.
    """
    record = utils.get_redcap_record(record_id)

    if record.event_id:
        event_string = "&event_id={}".format(record.event_id)
    else:
        event_string = ""

    redcap_url = '{}redcap_v{}/DataEntry/index.php?pid={}&id={}{}&page={}'
    redcap_url = redcap_url.format(record.url, record.redcap_version,
                                   record.project, record.record, event_string,
                                   record.instrument)

    return redirect(redcap_url)
