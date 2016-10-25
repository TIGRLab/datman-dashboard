from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD

app = Flask(__name__)
app.config.from_object('config')

#from app.database import db_session
db = SQLAlchemy(app)

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler, RotatingFileHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT),
                                'no-reply@kimellab.ca',
                                ADMINS,
                                'Dashboard failure',
                                credentials)
    file_handler = RotatingFileHandler('logs/dashboard.log',
                                       'a',
                                       1 * 1024 * 1024,
                                       10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.INFO)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    app.logger.addHandler(file_handler)
    app.logger.info('Dashboard startup')

from app import views, models
