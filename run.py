#!/usr/bin/env python
import os
from dashboard import app
import logging

logging.basicConfig(level=logging.DEBUG)
"""
Start a local webserver for the flask app
Useful for debug / development.

Some functionality (particularly file system access is disabled)

"""

if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0')
