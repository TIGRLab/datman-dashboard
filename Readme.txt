# Installation:

After cloning or copying this folder create a python virtual environment
and install the requirements with pip

- Create the virtual environment
  `$ virtualenv /usr/bin/python2.7`

- Activate the environment
  `$ source /venv/bin/activate`

- Install the requirements
  `$ pip install -r requirements.txt`


    **Note:** Some scripts now rely on the `datman.config` module:
    The `module load datman` command sets the `$PYTHONPATH` environment variable.
    This is a *bad thing* as PYTHONPATH overrides the virtualenv settings. See this
    [gist](https://gist.github.com/tomwright01/f98926c5ebdcb93ec9312d3c340a6445) describing how to modify venv/bin/activate to fix this.


## Creating the database

By default the data base is dashboard.sqlite

Database definition is contained in app/models.py

To create the database `python db_create.py`

To easily delete and recreate the database (avoiding problems with unique value
contraints) `db_clean.sh` then ~~`python populate_db.py`~~

~~To populate the database with sample data `python populate_db.py`~~

To populate the database with real data:

1. `add_study_info.py`
  This will add infomation gleaned from the site and study config files to the db

2. `python parse_qc.py`



# Starting the server

`python run.py`
