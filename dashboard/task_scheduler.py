#!/usr/bin/env python

import json
import logging
import requests
from requests import ConnectionError

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.base import run_job

from .exceptions import SchedulerException

logger = logging.getLogger(__name__)


class ContextThreadExecutor(ThreadPoolExecutor):
    """Runs all scheduler jobs within the app context.

    By default ThreadPoolExecutor does not propagate the app context correctly
    when it submits jobs to its pool to execute. This class fixes the problem
    by replacing the 'run_job' function submitted to the thread pool with
    the 'context_run' wrapper which ensures a context has been pushed before
    'run_job' executes.
    """

    def _do_submit_job(self, job, run_times):
        """Submits a job to the thread pool.

        This function is almost identical to BasePoolExecutor._do_submit_job
        from apscheduler.executors.pool as of version 3.6.3. The only change
        (aside from fixing line lengths) is to the call to self._pool.submit,
        where run_job has been replaced with context_run and the app has
        been added as an argument.
        """
        def callback(f):
            exc, tb = (
                f.exception_info() if hasattr(f, 'exception_info') else
                (f.exception(), getattr(f.exception(), '__traceback__', None))
            )
            if exc:
                self._run_job_error(job.id, exc, tb)
            else:
                self._run_job_success(job.id, f.result())

        f = self._pool.submit(
            context_run, self._scheduler.app, job, job._jobstore_alias,
            run_times, self._logger.name)
        f.add_done_callback(callback)


def context_run(app, job, jobstore_alias, run_times, logger_name):
    with app.app_context():
        return run_job(job, jobstore_alias, run_times, logger_name)


class RemoteScheduler(object):
    """A client scheduler that submits jobs to a scheduler server's API.

    This scheduler adds jobs via the dashboard server's scheduler API instead
    of directly interfacing with the job store. This is done to ensure that
    all jobs run from the server side only and never from an instance
    of the dashboard that has been imported.

    If more of the scheduler API needs to be exposed a list of all built in end
    points can found in flask_apscheduler/scheduler.py in
    'APScheduler._load_api'
    """

    def __init__(self, app=None):
        if app is None:
            # Delay init
            self.auth = (None, None)
            self.url = "N/A"
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
        user = app.config['SCHEDULER_USER']
        password = app.config['SCHEDULER_PASS']
        scheduler_server = app.config['SCHEDULER_SERVER_URL']

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

    def __repr__(self):
        return "<RemoteScheduler for {}>".format(self.url)


def format_job_function(job_function):
    return job_function.__module__ + ":" + job_function.__name__
