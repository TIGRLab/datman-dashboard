#!venv/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from dashboard import db
import os.path

""" Generic script to create a database that supports migration.
    Database locations are defined in config.py
    The data schema is read from models.py

CAUTION: This 'should' work with the postgres implementation but will
create a fresh **EMPTY** database.
It would be better to follow the instructions to restore a database from backup

###########################################
# Usage:
# $ source activate /archive/code/dashboard/venv/bin/activate
# $ module load /archive/code/datman_env.module
# $ module load /archive/code/dashboard.module
# $ ./db_create.py
#
############################################
    """



db.create_all()

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
