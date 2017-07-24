from dashboard import app
import logging

logging.basicConfig(level=logging.DEBUG)

"""
Needed for starting a local instance of the app using srv_uwsgi.sh
"""

if __name__ == '__main__':
	app.run()
