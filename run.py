#!python
import os
from app import app
import logging

logging.basicConfig(level=logging.DEBUG)
"""Start a local webserver for the flask app"""
# disable the debuggering pincode
os.environ["WERKZEUG_DEBUG_PIN"] = "off"
app.run(debug=True, host='0.0.0.0')
