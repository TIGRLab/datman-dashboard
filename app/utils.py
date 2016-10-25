"""Location for utility functions"""
import logging
import os
from subprocess import Popen, STDOUT, PIPE
import datman as dm

logger = logging.getLogger(__name__)
logger.info('loading utils')

CFG = dm.config.config()

class TimeoutError(Exception):
    pass


def _check_study(study):
    """Check if study is a valid study"""
    study = str(study)
    global CFG
    if study in CFG.site_config['Projects'].keys():
        return True
    return False


def get_todo(study=None, timeout=30):
    """Run to dm-qc-todo.py return the results as a dict
    Runs dm-qc-todo.py inside `timeout` to prevent blocking"""

    # As we are using subprocess with shell=True sanitize the input
    if study:
        if not _check_study(study):
            logger.error('Invalid study:{}'.format(study))
            return
        out = Popen(['timeout', str(timeout), "dm-qc-todo.py", "--study", str(study)],
                    stderr=STDOUT, stdout=PIPE)
    else:
        out = Popen(['timeout', str(timeout), "dm-qc-todo.py"],
                    stderr=STDOUT, stdout=PIPE)

    result = out.communicate()[0]
    if out.returncode == 124:
        logger.warning('dm-qc-todo timed out on study:{} with timeout:{}'
                       .format(study, timeout))
        raise TimeoutError
    if out.returncode != 0:
        logger.error('dm-qc-todo failed on study:{} with error:{}'
                     .format(study, result))
        raise RuntimeError

    output = {}
    if result:
        results = result.split('\n')
        for result in results:
            if len(result) > 0:  # last result is empty string
                result = result.split(':')
                output[result[0]] = result[1]

    return output


def get_qc_doc(session_name):
    global CFG

    try:
        i = dm.scanid.parse(str(session_name))
    except dm.scanid.ParseException:
        logger.warning('Invalid session name:{}'.format(session_name))
        return None

    qc_path = CFG.get_path('qc', study=i.study)
    qc_file = 'qc_{}.html'.format(i.get_full_subjectid_with_timepoint())
    qc_full_path = os.path.join(qc_path, i.get_full_subjectid_with_timepoint(), qc_file)

    if os.path.isfile(qc_full_path):
        return(qc_full_path)
    else:
        return None
