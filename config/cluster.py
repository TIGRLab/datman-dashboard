"""Configuration for job submission to a cluster.
"""
import os

# Command to use when submitting to cluster.
SUBMIT_COMMAND = os.environ.get("DASHBOARD_QSUBMIT_CMD") or "sbatch"

# Options to always set during submission (e.g. QOS)
SUBMIT_OPTIONS = os.environ.get("DASHBOARD_QSUBMIT_OPTIONS") or ""
