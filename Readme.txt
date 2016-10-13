# Installation:

After cloning or copying this folder create a python virtual environment
and install the requirements with pip

`$ virtualenv /usr/bin/python2.7`
`$ pip install -r requirements.txt`

By default the data base is dashboard.sqlite

Database definition is contained in app/models.py

To create the database `python db_create.py`
To populate the database with sample data `python populate_db.py`

To easily delete and recreate the database (avoiding problems with unique value
contraints) `db_clean.sh` then ` python populate_db.py`

# Starting the server

`python run.py`
