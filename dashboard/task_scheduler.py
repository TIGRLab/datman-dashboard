#!/usr/bin/env python

import json
import logging
import requests
from requests import ConnectionError

from .exceptions import SchedulerException

logger = logging.getLogger(__name__)


class RemoteScheduler(object):
    """
    This makes sure jobs are sent to the actual dashboard server rather than
    allowing each `import dashboard` to setup its own local scheduler.

    If more of the scheduler api needs to be exposed a list of all built in end
    points can found in flask_apscheduler/scheduler.py in
    'APScheduler._load_api'
    """

    def __init__(self, app):
        if not app:
            # Delay init
            self.auth = (None, None)
            return
        self.init_app(app)


    def add_job(self, job_id, job_function, **extra_args):
        if not self.url:
            logger.error("Can't submit job {}, scheduler URL not set".format(
                    job_id))
            return
        api_url = self.url + "/jobs"
        job_str = format_job_function(job_function)
        extra_args['id'] = job_id
        extra_args['run_date'] = str(extra_args['run_date'])
        extra_args['func'] = job_str
        json_payload = json.dumps(extra_args)
        try:
            response = requests.post(api_url,
                                     data=json_payload,
                                     auth=self.auth)
        except ConnectionError:
            raise SchedulerException("Scheduler API is not available at {}"
                                     "".format(self.url))
        if response.status_code == 401:
            raise SchedulerException("Can't submit job, access denied. Check "
                                     "that username and password are "
                                     "correctly configured")
        if response.status_code != 200:
            raise SchedulerException("Failed to submit job to scheduler. "
                                     "Received status code {} and response "
                                     "{}".format(response.status_code,
                                                 response.content))

        # If we later intend to do anything with the jobs this should
        # be updated to return a proper apscheduler.Job instance (like the
        # 'real' scheduler), but for now its fine to return the string
        # formatted dictionary the server gives us
        return response.content

    def init_app(self, app):
        user = app.config('SCHEDULER_USER')
        password = app.config('SCHEDULER_PASS')
        url = app.config('SCHEDULER_SERVER_URL')

        self.auth = (user, password)
        if scheduler_server:
            if not (scheduler_server.startswith("https://") or
                    scheduler_server.startswith("http://")):
                scheduler_server = "http://" + scheduler_server
            self.url = scheduler_server + "/scheduler"
        else:
            self.url = ""
        return

    def start(self):
        # This is here to allow delayed initialization
        return


def format_job_function(job_function):
    return job_function.__module__ + ":" + job_function.__name__
