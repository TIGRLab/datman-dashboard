#!/bin/bash
# Start the app in a server on your local machine.
# Useful for debug / development
# Use the WERKZEUG server (run.py) if you need detailed code debuggering

uwsgi --plugins-dir /usr/lib/uwsgi/ --need-plugin python --socket 0.0.0.0:5001 --protocol=http --wsgi-file wsgi.py --callable app --enable-threads --static-map /archive=/mnt/tigrlab/archive
