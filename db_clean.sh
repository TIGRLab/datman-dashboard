#!/bin/bash

#delete and recreate the dashboard.sqlite database

echo -n "This will delete all data in dashboard.sqlite!!!"
echo -n "Are you sure (type 'Yes' to continue):"
read text
if [ "$text" = "Yes" ];
then
  rm dashboard.sqlite
  rm -R db_repository
  python db_create.py
fi
