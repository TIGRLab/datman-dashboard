import os
import logging
import re

logger = logging.getLogger(__name__)


def get_run_log(log_dir, study, done_regex, error_regex):
    log_file = os.path.join(log_dir, f"{study}_latest.log")
    output = {}
    output["contents"] = read_log(log_file)
    output["header"] = make_header_msg(
        output["contents"], done_regex, error_regex)
    return output


def read_log(log_file):
    try:
        with open(log_file, "r") as contents:
            result = contents.readlines()
    except Exception as e:
        logger.error(f"Failed to read run log file {log_file}. {e}")
        return ""
    result = [line.replace("\n", "<br>") for line in result]
    return "<br>".join(result)


def make_header_msg(log_contents, done_regex, error_regex):
    if not re.search(done_regex, log_contents):
        return "Running..."
    error_count = len(re.findall(error_regex, log_contents))
    return f"{error_count} errors reported"
