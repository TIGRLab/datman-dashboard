#!python

from app import app
import logging

logging.basicConfig(level=logging.DEBUG)
"""Start a local webserver for the flask app"""

app.run(debug=True, host='0.0.0.0')
