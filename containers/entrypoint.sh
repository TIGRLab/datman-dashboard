#!/bin/bash

# This is used by docker-compose.yml to ensure the postgres database schema is
# kept up to date

cd /dashboard/
flask db upgrade
uwsgi --socket=0.0.0.0:5000 --protocol=http --wsgi-file=/dashboard/wsgi.py --callable=app --enable-threads
