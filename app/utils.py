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
                if len(result) > 1:
                    # got a valid qc doc
                    session_name = result[0].split('/')[-2]
                    output[session_name] = [result[0], result[1]]
                else:
                    session_name = result[0].split('/')[-1]
                    output[session_name] = [result[0].split('/', 1)[1],
                                            result[0].split('/', 1)[0]]

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


def update_checklist(session_name, comment, checklist_file=None):
    """
    Searches for the checklist file identified by session_name
    creates the file if it doesn't exist
    Updates the file with the new comment (if it's different from the existing
    comment).
    Returns:
    True on success, nothing otherwise
    Arguments:
        session_name: full session name, e.e. "SPN01_CMH_0001_01"
        comment: string
        checklist_file: if None then checklist is identified from session_name
    """
    global CFG
    if not checklist_file:
        try:
            ident = dm.scanid.parse(session_name)
        except dm.scanid.ParseException:
            logger.warning('Invalid session name:{}'.format(session_name))
            return

        study_name = CFG.map_xnat_archive_to_project(session_name)
        if not study_name:
            logger.warning('session name: {} not recoginzed'.format(session_name))
            return

        checklist = os.path.join(CFG.get_path('meta', study_name), 'checklist.csv')
    else:
        checklist = checklist_file

    if not os.path.isfile(checklist):
        logger.warning('Checklist file:{} not found, creating')

    try:
        with open(checklist, 'r') as cl_file:
            lines = cl_file.readlines()
    except IOError:
        logger.warning('Failed to open checklist file:{}'.format(checklist))
        lines = []

    target_idx = None
    existing_comment = None
    for idx, val in enumerate(lines):
        parts = val.split(' ')

        # split off the file extension part
        scan_id = parts[0].split('.')[0]
        if scan_id == 'qc_{}'.format(session_name):
            target_idx = idx
            try:
                #  ensure to get rid of trailing newline
                existing_comment = parts[1]
            except KeyError:
                existing_comment = ''
            break

    if not target_idx:
        logger.warning('Entry:{} not found in checklist:{}, adding.'
                       .format(session_name, checklist))
        with open(checklist, 'a+') as cl_file:
            cl_file.write('qc_{}.html {}\n'.format(session_name, comment))
        return True

    # ensure to get rid of whitespace, trailing newlines etc
    comment = comment.strip()
    existing_comment = existing_comment.strip()

    if not existing_comment == comment:
        lines[target_idx] = 'qc_{}.html {}\n'.format(session_name, comment)

        with open(checklist, 'w+') as cl_file:
            cl_file.writelines(lines)

    return True
