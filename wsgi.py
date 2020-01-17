#!/usr/bin/env python
"""Start the dashboard using Flask's built in webserver

This is used to start the app for debug / development on a local machine.

This script is also used by flask migrate and srv_uwsgi.sh.
"""
from dashboard import create_app

app = create_app()

if __name__ == '__main__':
	app.run(threaded=True, host='0.0.0.0')
