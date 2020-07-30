"""Code used to interact with computing clusters.
"""
from os.path import join
from subprocess import run, PIPE
import logging

from flask import current_app

logger = logging.getLogger(__name__)

def submit_job(script, input_args=None, job_name=None, work_dir=None):
    """Attempt to submit a job to the configured computing cluster.

    Args:
        script (str): The full path to the script to run as a queue job.
        input_args (:obj:`list`, optional): A list of input arguments to give
            the job script.
        job_name (str, optional): The name to give the job.
        work_dir (str, optional): The directory to use as the work dir.
            A directory will be created in /tmp if none is given.
    """
    cmd = [current_app.config["SUBMIT_COMMAND"]]

    if current_app.config["SUBMIT_OPTIONS"]:
        cmd.append(current_app.config["SUBMIT_OPTIONS"])

    cmd.append(script)

    if input_args:
        cmd.extend(input_args)

    try:
        # capture_output=True can be used only for python > 3.5
        result = run(cmd, stdout=PIPE, stderr=PIPE)
    except Exception:
        logger.error(
            "Failed to submit queue job '{}' with input args '{}'.".format(
                script, input_args
            )
        )
        raise

    try:
        result.check_returncode()
    except CalledProcessError:
        logger.error(
            "An error occurred during submission of script '{}' with input "
            "args '{}'.".format(script, input_args)
        )
        raise
