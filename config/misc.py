"""Miscellaneous settings
"""
import os

from .utils import read_boolean

# Name of the repository on github that hosts the issues
GITHUB_REPO = os.environ.get('GITHUB_ISSUES_REPO')

# Username that owns GITHUB_REPO
GITHUB_OWNER = os.environ.get('GITHUB_ISSUES_OWNER')

# Whether GITHUB_REPO is a public repository. Set to False if private
GITHUB_PUBLIC = read_boolean('GITHUB_ISSUES_PUBLIC', default=True)

# The REDCap token to use when retrieving records after a data entry trigger
REDCAP_TOKEN = os.environ.get('REDCAP_TOKEN')

# Metrics to display.
# NOTE: The code that uses this is currently broken and might be scrapped
# entirely
DISPLAY_METRICS = {
    'phantom': {
        't1': ['c1', 'c2', 'c3', 'c4'],
        'dti': ['AVENyqratio', 'AVE Ave.radpixshift',
                'AVE Ave.colpixshift', 'aveSNR_dwi'],
        'fmri': ['sfnr', 'rdc']},
    'human': {
        't1': [],
        'dti': ['tsnr_bX', 'meanRELrms', '#ndirs', 'Spikecount'],
        'fmri': ['mean_fd', 'mean_sfnr', 'ScanLength']}
}
