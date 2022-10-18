"""Tests for classes in dashboard.models
"""

import pytest

from tests.utils import query_db, add_studies
from dashboard import models


class TestUser:

    def test_get_sites_returns_all_sites_avail_for_user(self):
        user = models.User.query.get(1)
        result = user.get_sites()
        expected = self.get_result(
            "SELECT DISTINCT ss.site"
            "  FROM users as u, study_users as su, study_sites as ss"
            "  WHERE u.id = su.user_id"
            "    AND u.id = 1"
            "    AND su.study = ss.study"
            "    AND (su.site IS NULL OR su.site = ss.site)"
        )
        assert sorted(result) == sorted(expected)

    def test_get_sites_doesnt_duplicate_site_names(self):
        user = models.User.query.get(1)
        result = user.get_sites()
        expected = list(set(result))
        assert sorted(result) == sorted(expected)

    def test_get_sites_returns_list_of_strings_for_reg_user(self):
        user = models.User.query.get(1)
        result = user.get_sites()

        assert all(isinstance(item, str) for item in result)

    def test_get_sites_returns_list_of_strings_for_admin_user(self):
        admin = models.User.query.get(2)
        assert admin.dashboard_admin is True

        result = admin.get_sites()
        assert all(isinstance(item, str) for item in result)

    def get_result(self, sql_query):
        return [item[0] for item in query_db(sql_query)]


@pytest.fixture(autouse=True)
def user_records(dash_db):
    """Adds some user records and access permissions for testing.
    """
    user = models.User("Donald", "Duck")
    admin = models.User("Mickey", "Mouse", dashboard_admin=True)
    dash_db.session.add(user)
    dash_db.session.add(admin)
    dash_db.session.commit()
    assert user.id == 1
    assert admin.id == 2

    add_studies({
        "STUDY1": {
            "CMH": [],
            "UTO": []
        },
        "STUDY2": {
            "CMH": []
        },
        "STUDY3": {
            "ABC": []
        }
    })

    user.add_studies({
        "STUDY1": ["CMH"],
        "STUDY2": [],
        "STUDY3": []
    })

    return dash_db
