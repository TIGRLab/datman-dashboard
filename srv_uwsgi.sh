#!/bin/bash

# Start the dashboard in uwsgi's webserver
#
# uwsgi must be installed. Gives less detailed debugging info than
# using flask's built in server, but allows you to ensure code will work
# the same as on the production server which also uses uwsgi.

uwsgi --plugins-dir /usr/lib/uwsgi/ \
      --socket 0.0.0.0:5000 \
      --protocol=http \
      --wsgi-file wsgi.py \
      --callable app \
      --enable-threads \
      --static-map /archive=/mnt/tigrlab/archive
