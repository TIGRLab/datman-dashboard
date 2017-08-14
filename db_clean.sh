#!/bin/bash

#delete and recreate the dashboard.sqlite database

# DEPRECATED: This only supports a test environment. Database management
# should be performed through standard postgres tools.


###########################################
# Usage:
# $ source activate /archive/code/dashboard/venv/bin/activate
# $ module load /archive/code/datman_env.module
# $ module load /archive/code/dashboard.module
# $ ./db_clean.sh
#
############################################

echo -n "This will delete all data in dashboard.sqlite!!!"
echo -n "Are you sure (type 'Yes' to continue):"
read text
if [ "$text" = "Yes" ];
then
  rm dashboard.sqlite
  rm -R db_repository
  python db_create.py
fi
