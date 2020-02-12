"""Logging settings
"""
import os
import logging
from logging.handlers import DEFAULT_TCP_LOGGING_PORT
from pathlib import Path

from .utils import BASE_DIR, ENV, DEBUG
from .email import (LOG_MAIL_SERVER, LOG_MAIL_PORT, LOG_MAIL_USER,
                    LOG_MAIL_PASS, ADMINS, SENDER)
from .scheduler import SCHEDULER_ENABLED


# Default log level to use for all dashboard logging
LOG_LEVEL = os.environ.get('DASH_LOG_LEVEL') or 'DEBUG'

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'basic': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s [%(name)s] %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
            'formatter': 'basic'
        }
    },
    'loggers': {
        'dashboard': {
            'level': LOG_LEVEL,
            'handlers': ['console']
        },
        # Silence datman logging
        'datman': {
            'level': logging.CRITICAL
        }
    }
}

# The server name/IP to send log messages to. If not provided, server logging
# will always be disabled.
LOG_SERVER = os.environ.get("DASHBOARD_LOG_SERVER")

if LOG_SERVER:
    # The port on LOG_SERVER to forward logs to
    LOG_PORT = (os.environ.get("DASHBOARD_LOG_SERVER_PORT")
                or DEFAULT_TCP_LOGGING_PORT)
    LOGGING_CONFIG['handlers']['server'] = {
        'class': 'logging.handlers.SocketHandler',
        'host': LOG_SERVER,
        'port': LOG_PORT,
        'level': LOG_LEVEL,
        'formatter': 'basic',
    }
    LOGGING_CONFIG['loggers']['dashboard']['handlers'].append('server')

if not DEBUG and LOG_MAIL_SERVER:
    if LOG_MAIL_USER or LOG_MAIL_PASS:
        credentials = (LOG_MAIL_USER, LOG_MAIL_PASS)
    else:
        credentials = None

    LOGGING_CONFIG['handlers']['email'] = {
        'class': 'logging.handlers.SMTPHandler',
        'mailhost': (LOG_MAIL_SERVER, LOG_MAIL_PORT),
        'fromaddr': SENDER,
        'toaddrs': ADMINS,
        'subject': 'Dashboard failure',
        'credentials': credentials,
        'formatter': 'basic',
        'level': 'ERROR'
    }
    LOGGING_CONFIG['loggers']['dashboard']['handlers'].append('email')

if DEBUG and ENV == 'development':
    # The directory to save file logs to
    user_dir = os.environ.get('DASH_LOG_DIR')
    LOG_DIR = Path(user_dir) if user_dir else BASE_DIR / 'logs'
    LOG_DIR.mkdir(mode=0o755, parents=False, exist_ok=True)

    DEST_LOG = LOG_DIR / 'dashboard.log'
    try:
        DEST_LOG.touch()
    except (PermissionError, FileNotFoundError):
        pass
    else:
        LOGGING_CONFIG['handlers']['log_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': DEST_LOG,
            'mode': 'a',
            'maxBytes': 1 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'basic',
            'level': LOG_LEVEL,
        }
        LOGGING_CONFIG['loggers']['dashboard']['handlers'].append('log_file')

if SCHEDULER_ENABLED:
    LOGGING_CONFIG['loggers']['apscheduler'] = {
        'level': LOG_LEVEL,
        'handlers': LOGGING_CONFIG['loggers']['dashboard']['handlers']
    }
