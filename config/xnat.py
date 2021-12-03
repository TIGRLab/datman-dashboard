"""Configuration for XNAT integration
"""
import os

from .utils import read_boolean

XNAT_ENABLED = read_boolean('DASH_ENABLE_XNAT')

# These can be omitted as long as an XnatCredentials file was configured
# in the datman configuration files
XNAT_USER = os.environ.get('XNAT_USER')
XNAT_PASS = os.environ.get('XNAT_PASS')

# If one or the other is defined, both must be
if XNAT_ENABLED and (XNAT_USER or XNAT_PASS) and not (XNAT_USER and XNAT_PASS):
    logger.error("XNAT_USER or XNAT_PASS undefined, xnat integration will "
                 "be disabled.")
    XNAT_ENABLED = False
