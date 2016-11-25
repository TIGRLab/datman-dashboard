#!/bin/bash
uwsgi --plugins-dir /usr/lib/uwsgi/ --need-plugin python --socket 0.0.0.0:5001 --protocol=http --wsgi-file wsgi.py --callable app --enable-threads --static-map /archive=/mnt/tigrlab/archive
