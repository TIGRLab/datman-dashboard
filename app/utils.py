"""Location for utility functions"""
import logging
from subprocess import Popen, STDOUT, PIPE
import datman as dm

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def _check_study(study):
    """Check if study is a valid study"""
    study = str(study)
    cfg = dm.config.config()
    if study in cfg.site_config['Projects'].keys():
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
                     .format(study, result[0]))
        raise RuntimeError

    output = {}
    if result:
        results = result.split('\n')
        for result in results:
            if len(result) > 0:  # last result is empty string
                result = result.split(':')
                output[result[0]] = result[1]

    return output
