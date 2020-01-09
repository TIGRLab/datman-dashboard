#!/usr/bin/env python
"""Start a local webserver for the dashboard

Useful for debug / development.

"""
from dashboard import create_app
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
   app = create_app()
   app.run(threaded=True, host='0.0.0.0')
