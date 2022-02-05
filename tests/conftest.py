"""Creates fixtures to ensure all tests run against a test database.

This creates a test database at the start of the test session and wipes it
clean after every test. The user you connect to postgres with must have
permissions to create a new database.
"""

import pytest
from sqlalchemy_utils import database_exists, create_database, drop_database

import dashboard


@pytest.fixture(scope="session")
def dash_app(request):
    app = dashboard.create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config[
        "SQLALCHEMY_TEST_DATABASE_URI"
    ]

    if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
        create_database(app.config["SQLALCHEMY_DATABASE_URI"])

    yield app
    drop_database(app.config["SQLALCHEMY_DATABASE_URI"])


@pytest.fixture(scope="function")
def dash_db(dash_app):
    with dash_app.app_context():
        dashboard.models.db.create_all()
        yield dashboard.models.db
        # If you remove this line the session will remain open and
        # the tables wont be able to drop, causing the tests to freeze
        dashboard.models.db.session.remove()
        dashboard.models.db.drop_all()
