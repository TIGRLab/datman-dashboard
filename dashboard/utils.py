"""Location for utility functions"""
import logging
import os
from subprocess import Popen, STDOUT, PIPE
import datman.config
import datman.scanid

DM_QC_TODO = '/archive/code/datman/bin/dm-qc-todo.py'
logger = logging.getLogger(__name__)
logger.info('loading utils')

CFG = datman.config.config()

class TimeoutError(Exception):
    pass


def get_study_name(str):
    """
    'get_study_name' Convert a study identifier to a study name

    >>> get_study_name('SPN01')
    "SPINS"
    """
    return CFG.map_xnat_archive_to_project(str)


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
        out = Popen(['timeout', str(timeout), DM_QC_TODO, "--study", str(study)],
                    stderr=STDOUT, stdout=PIPE)
    else:
        out = Popen(['timeout', str(timeout), DM_QC_TODO],
                    stderr=STDOUT, stdout=PIPE)

    result = out.communicate()[0]
    if out.returncode == 124:
        logger.warning('dm-qc-todo timed out on study:{} with timeout:{}'
                       .format(study, timeout))
        raise TimeoutError
    if out.returncode != 0:
        logger.error('dm-qc-todo failed on study:{} with error:{}'
                     .format(study, result))
        raise RuntimeError(result)

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
    """
    Returns the path to a sessions html qc doc
    """
    global CFG

    try:
        i = datman.scanid.parse(str(session_name))
    except datman.scanid.ParseException:
        logger.warning('Invalid session name:{}'.format(session_name))
        return None

    qc_path = CFG.get_path('qc', study=session_name)
    qc_file = 'qc_{}.html'.format(i.get_full_subjectid_with_timepoint())
    qc_full_path = os.path.join(qc_path, i.get_full_subjectid_with_timepoint(), qc_file)

    if os.path.isfile(qc_full_path):
        return(qc_full_path)
    else:
        return None

def update_blacklist(scan_name, comment, blacklist_file=None, study_name=None):
    """
    Searches for the blacklist file identified by scan_name and creates the file
    if it doesn't exist. Updates the file with the new comment (if it's
    different from the existing comment).

    Set comment to 'None' or an empty string to remove an existing entry

    Returns:    True on success, otherwise will raise an exception

    Arguments:
        scan_name:              full scan name minus the extension, e.g.
                                "SPN01_CMH_0044_01_01_EMP_11_AxEPI-EATask1"
        comment:                A string or None to delete an entry
        blacklist_file:         The blacklist file to update. If unset, the scan
                                name will be used to try to find the a file
                                named 'blacklist.csv' in the study's metadata
                                folder
    """

    if not blacklist_file:
        if not study_name:
            try:
                ident, _, _, _ = datman.scanid.parse_filename(scan_name)
            except datman.scanid.ParseException:
                raise datman.scanid.ParseException(
                        'Invalid scan_name: {}'.format(scan_name))
            try:
                # If something goes wrong this could raise a variety of
                # exceptions... just trapping and reporting all for now - Dawn
                study_name = CFG.map_xnat_archive_to_project(
                        ident.get_full_subjectid_with_timepoint())
            except Exception as e:
                raise type(e)("Could not identify study for scan name {}. "
                        "Reason: {}".format(scan_name, e.message))
        blacklist = os.path.join(CFG.get_path('meta', study_name),
                'blacklist.csv')
    else:
        blacklist = blacklist_file

    if not os.path.isfile(blacklist):
        logger.info('Blacklist file {} not found, creating'.format(blacklist))

    try:
        with open(blacklist, 'r') as cl_file:
            lines = cl_file.readlines()
    except IOError:
        logger.warning('Failed to open blacklist file: {}'.format(blacklist))
        lines = []

    target_idx = None
    existing_comment = ""
    for idx, val in enumerate(lines):
        if not val.strip(): # deal with blank lines
            continue
        parts = val.split(None, 1)
        if scan_name == parts[0]:
            target_idx = idx
            try:
                #  ensure to get rid of trailing newline
                existing_comment = parts[1]
            except (KeyError, IndexError):
                existing_comment = ''
            break

    if comment:
        comment = comment.strip()
        existing_comment = existing_comment.strip()

        if not existing_comment == comment:
            lines[target_idx] = '{}\t{}\n'.format(scan_name, comment)
    else:
        if target_idx is None:
            # No comment to add, and no entry to delete
            return True
        # Delete entry
        del lines[target_idx]

    if target_idx is None:
        # Only need to add a new line to the end of the file
        with open(blacklist, 'a+') as cl_file:
            cl_file.write('{}\t{}\n'.format(scan_name, comment))
        return True
    else:
        # Rewrite all lines to update the comment
        with open(blacklist, 'w+') as cl_file:
            cl_file.writelines(lines)
    return True


def update_checklist(session_name, comment, checklist_file=None, study_name=None):
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
            ident = datman.scanid.parse(session_name)
        except datman.scanid.ParseException:
            logger.warning('Invalid session name:{}'.format(session_name))
            return

        if not study_name:
            try:
                study_name = CFG.map_xnat_archive_to_project(session_name)
            except KeyError:
                logger.warning('session name: {} not recoginzed'.format(session_name))
                return

        checklist = os.path.join(CFG.get_path('meta', study_name), 'checklist.csv')
    else:
        checklist = checklist_file

    if not os.path.isfile(checklist):
        logger.warning('Checklist file:{} not found, creating'.format(checklist))
    try:
        with open(checklist, 'r') as cl_file:
            lines = cl_file.readlines()
    except IOError:
        logger.warning('Failed to open checklist file:{}'.format(checklist))
        lines = []

    target_idx = None
    found = False
    existing_comment = None
    for idx, val in enumerate(lines):
        if not val.strip(): # deal with blank lines
            continue
        parts = val.split(None, 1)

        scan_id = parts[0].split('.')[0]
        if scan_id == 'qc_{}'.format(session_name):
            found = True
            target_idx = idx
            try:
                #  ensure to get rid of trailing newline
                existing_comment = parts[1]
            except (KeyError, IndexError):
                existing_comment = ''
            break

    if not found:
        logger.warning('Entry:{} not found in checklist:{}, adding.'
                       .format(session_name, checklist))
        logger.info('Running as user:{}'.format(os.getuid()))
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

def get_export_info(study, site):
    export_info = CFG.get_exportinfo(site=site, study=study)
    return export_info

def get_study_folder(study, folder_type=None):
    """
    Returns the base filesystem path for the study.
    If folder is supplied and is defined in study config
    then path to the foder is returned

    >>> get_study_folder('TEST', 'nii')
    /archive/data/TEST/data/nii/
    """
    try:
        if folder_type:
            path = CFG.get_path(folder_type, study)
        else:
            path = CFG.get_study_base(study=study)
    except KeyError:
        logger.error('Failed to find folder:{} for study:{}'
                     .format(folder_type, study))
        return None
    return path
