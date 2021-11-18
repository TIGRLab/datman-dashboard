"""Code + variables that may be needed when setting other configuration
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ENV = os.environ.get('FLASK_ENV') or 'production'
DEBUG = bool(os.environ.get('FLASK_DEBUG') or (ENV and 1))


def read_boolean(var_name, default=False):
    """Reads an environment variable and ensures a boolean is returned

    Args:
        var_name (str): An environment variable to check
        default (bool, optional): The value to use as the default for var_name

    Returns:
        bool
    """
    try:
        result = os.environ.get(var_name).lower()
    except AttributeError:
        result = ""
    if result == "":
        return default
    if result == 'true' or result == 'on':
        return True
    return False
