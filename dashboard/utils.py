"""Location for utility functions"""
import logging
import os
from subprocess import Popen, STDOUT, PIPE

from github import Github

from dashboard import GITHUB_OWNER, GITHUB_REPO
import datman.config
import datman.scanid

DM_QC_TODO = '/archive/code/datman/bin/dm-qc-todo.py'
logger = logging.getLogger(__name__)
logger.info('loading utils')

CFG = datman.config.config()

class TimeoutError(Exception):
    pass

def search_issues(token, timepoint):
    search_string = "{} repo:{}/{}".format(timepoint, GITHUB_OWNER, GITHUB_REPO)
    try:
        issues = Github(token).search_issues(search_string)
    except:
        return None
    result = sorted(issues, key=lambda x: x.created_at)
    return result

def get_issue(token, issue_num=None):
    if not issue_num:
        return None
    try:
        repo = get_issues_repo(token)
        issue = repo.get_issue(issue_num)
    except Exception as e:
        logger.error("Can't retrieve issue {}. Reason: {}".format(issue_num, e))
        issue = None
    return issue

def create_issue(token, title, body, assign=None):
    try:
        repo = get_issues_repo(token)
        if assign:
            issue = repo.create_issue(title, body, assignee=assign)
        else:
            # I thought a default of None would be a clever way to avoid needing
            # an if/else here but it turns out 'assignee' will raise a
            # mysterious exception when set to None :( So... here we are
            issue = repo.create_issue(title, body)
    except Exception as e:
        raise Exception("Can't create new issue '{}'. Reason: {}".format(title,
                e))
    return issue

def get_issues_repo(token):
    try:
        repo = Github(token).get_user(GITHUB_OWNER).get_repo(GITHUB_REPO)
    except Exception as e:
        raise Exception("Can't retrieve github issues repo. {}".format(e))
    return repo


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


def get_study(datman_name):
    """
    Returns the name of the study for a datman style session name or scan name
    """
    if datman.scanid.is_scanid(datman_name):
        try:
            ident = datman.scanid.parse(datman_name)
        except datman.scanid.ParseException:
            raise datman.scanid.ParseException("Invalid datman ID: {}".format(
                    datman_name))
    else:
        try:
            ident, _, _, _ = datman.scanid.parse_filename(datman_name)
        except datman.scanid.ParseException:
            raise datman.scanid.ParseException("Invalid scan name: {}".format(
                    datman_name))
    try:
        # If something goes wrong this could raise a variety of
        # exceptions... just trapping and reporting all for now - Dawn
        study = CFG.map_xnat_archive_to_project(
                ident.get_full_subjectid_with_timepoint())
    except Exception as e:
        raise type(e)("Could not identify study for scan name {}. "
                "Reason - {}".format(datman_name, e))
    return study


def find_metadata(default_name, user_file=None, study=None):
    if user_file:
        if not os.path.isfile(user_file):
            logger.warning("File {} does not exist.".format(user_file))
        found_file = user_file
    else:
        if not study:
            raise RuntimeError("Can't locate metadata file {}. "
                    "Study not given.".format(default_name))
        found_file = os.path.join(CFG.get_path('meta', study), default_name)
    return found_file


def get_contents(file_name):
    """
    Try to read the contents of <file_name> or return an empty list if exception
    occurs
    """
    try:
        with open(file_name, 'r') as fh:
            lines = fh.readlines()
    except IOError as e:
        logger.error('Failed to open file: {}. Reason - {}'.format(file_name,
                e))
        lines = []
    return lines

def get_metadata_entry(contents, match_str):
    target_idx = None
    existing_comment = ""
    for idx, val in enumerate(contents):
        if not val.strip(): # deal with blank lines
            continue
        parts = val.split(None, 1)

        if parts[0] == match_str:
            target_idx = idx
            try:
                existing_comment = parts[1]
            except IndexError:
                existing_comment = ''
            existing_comment = existing_comment.strip()
            break

    return target_idx, existing_comment


def update_blacklist(scan_name, comment=None, blacklist_file=None, study_name=None):
    """
    Updates the blacklist file with a new entry or updates an existing entry.
    Set comment to 'None' or an empty string to delete an existing entry.

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
    if not study_name:
        study_name = get_study(scan_name)

    blacklist = find_metadata('blacklist.csv', user_file=blacklist_file,
            study=study_name)

    lines = get_contents(blacklist)
    index, _ = get_metadata_entry(lines, scan_name)

    if index is None and comment:
        ## Add a new blacklist entry to end of the list
        with open(blacklist, 'a+') as cl_file:
            cl_file.write('{}\t{}\n'.format(scan_name, comment))
        return True

    if index is None:
        # No entry found and no comment to add, exit early and do nothing.
        return True

    # Otherwise, either update a comment or delete existing entry if
    # comment wasnt given
    if comment:
        lines[index] = '{}\t{}\n'.format(scan_name, comment)
    else:
        del lines[index]

    # Rewrite whole file to make the update
    with open(blacklist, 'w+') as cl_file:
        cl_file.writelines(lines)

    return True


def update_checklist(session_name, comment, checklist_file=None, study_name=None):
    """
    Adds a new comment to the checklist file or updates an existing entry.

    Returns: True on success, nothing otherwise

    Arguments:
        session_name: full session name, e.e. "SPN01_CMH_0001_01"
        comment: string
        checklist_file: if None then checklist is identified from session_name
    """
    qc_page_name = "qc_{}.html".format(session_name)

    if not study_name:
        study_name = get_study(session_name)

    checklist = find_metadata('checklist.csv', user_file=checklist_file,
            study=study_name)

    lines = get_contents(checklist)
    index, existing_comment = get_metadata_entry(lines, qc_page_name)

    if index is None:
        logger.warning('Entry {} not found in checklist file {}, adding.'
                       .format(session_name, checklist))
        logger.info('Running as user: {}'.format(os.getuid()))
        with open(checklist, 'a+') as cl_file:
            cl_file.write('{} {}\n'.format(qc_page_name, comment))
        return True

    # ensure to get rid of whitespace, trailing newlines etc
    comment = comment.strip()
    existing_comment = existing_comment.strip()
    if not existing_comment == comment:
        lines[index] = 'qc_{}.html {}\n'.format(session_name, comment)
        with open(checklist, 'w+') as cl_file:
            cl_file.writelines(lines)


    return True

def get_export_info(study, site):
    export_info = CFG.get_exportinfo(site=site, study=study)
    return export_info

def get_study_path(study, folder=None):
    """
    Returns the full path to the study on the file system.

    If folder is supplied and is defined in study config
    then path to the foder is returned instead.
    """
    if folder:
        try:
            path = CFG.get_path(folder, study)
        except Exception as e:
            logger.error("Failed to find folder {} for study {}. Reason: {}"
                    "".format(folder, study, e))
            path = None
        return path

    try:
        path = CFG.get_study_base(study=study)
    except Exception as e:
        logger.error("Failed to find path for {}. Reason: {}".format(study, e))
        path = None
    return path
