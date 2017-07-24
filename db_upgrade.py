#!venv/bin/python
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

"""

Generic script to apply migration script generated using db_migrate.py

CAUTION: Probably still works since migration to postgres but this facility
is now better handled with database backups.

###########################################
# Usage:
# $ source activate /archive/code/dashboard/venv/bin/activate
# $ module load /archive/code/datman_env.module
# $ module load /archive/code/dashboard.module
# $ ./db_migrate.py
# $ ./db_upgrade.py
#
############################################

"""

api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('Current database version: ' + str(v))
