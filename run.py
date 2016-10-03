#!python

from app import app

"""Start a local webserver for the flask app"""

app.run(debug=True, host='0.0.0.0')
