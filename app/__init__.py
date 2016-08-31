from flask import Flask
import flask_sqlalchemy

app = Flask(__name__)
app.config.from_object('config')

from app.database import db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
