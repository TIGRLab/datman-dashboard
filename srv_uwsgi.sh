#!/bin/bash
uwsgi --socket 0.0.0.0:5001 --protocol=http -w wsgi:app --enable-threads --static-map /archive=/mnt/tigrlab/archive
