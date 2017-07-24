#!venv/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

"""
Generic script to revert a migration enabled database by one revision.

Caution: Untested on postgres, should probably restore a backup instead of trying this

###########################################
# Usage:
# $ source activate /archive/code/dashboard/venv/bin/activate
# $ module load /archive/code/datman_env.module
# $ module load /archive/code/dashboard.module
# $ ./db_downgrade.py
#
############################################
"""

v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
api.downgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, v - 1)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(v))
