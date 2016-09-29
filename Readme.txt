By default the data base is dashboard.sqlite

Database definition is contained in app/models.py

To create the database `python db_create.py`
To populate the database with sample data `python populate_db.py`

To easily delete and recreate the database (avoiding problems with unique value
contraints) `db_clean.sh` then ` python populate_db.py`
