#!/usr/bin/env python
"""Start the dashboard using Flask's built in webserver

This is used to start the app for debug / development on a local machine.

This script is also used by flask migrate. If it is deleted or renamed
the FLASK_APP variable will need to be set to get migrations to work.
"""
from dashboard import create_app

app = create_app()

if __name__ == '__main__':
	app.run(threaded=True, host='0.0.0.0')
