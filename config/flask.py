"""Flask built-in settings
"""
import os

# This should never be False for security reasons.
WTF_CSRF_ENABLED = True
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

if not SECRET_KEY:
    raise RuntimeError(
        "Must have 'FLASK_SECRET_KEY' set to start the app. This setting is "
        "used to encrypt session information and cookies and should be a "
        "random / hard to guess string.")
