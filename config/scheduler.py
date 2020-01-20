"""Configuration for job scheduling
"""
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler.auth import HTTPBasicAuth

from .utils import read_boolean
from .database import SQLALCHEMY_DATABASE_URI

SCHEDULER_JOBSTORES = {
    'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
}

SCHEDULER_JOB_DEFAULTS = {
    'coalesce': True,
    'misfire_grace_time': 3600
}

SCHEDULER_EXECUTORS = {
    'default':
        {'type': 'threadpool',
         'max_workers': 2}
}

# Indicates whether to start the scheduler server. Should only be set if
# the dashboard is being run through a webserver (i.e. not just imported)
SCHEDULER_ENABLED = read_boolean("DASHBOARD_SCHEDULER")

if SCHEDULER_ENABLED:
    # Controls whether to allow remote job submission (over HTTP)
    SCHEDULER_API_ENABLED = read_boolean("DASHBOARD_SCHEDULER_API")

    if SCHEDULER_API_ENABLED:
        # Password protect the API. This should never be used over the open
        # internet unless HTTPS is being used
        SCHEDULER_AUTH = HTTPBasicAuth()

else:
    SCHEDULER_API_ENABLED = False

# Username to use when submitting jobs. Credentials must match on server and
# clients.
SCHEDULER_USER = os.environ.get('DASHBOARD_SCHEDULER_USER')

# Password to use when submitting jobs. Credentials must match on server and
# clients.
SCHEDULER_PASS = os.environ.get('DASHBOARD_SCHEDULER_PASS')

# The server URL to send scheduled jobs to. (Client/imported instances only)
SCHEDULER_SERVER_URL = os.environ.get("DASHBOARD_URL")
