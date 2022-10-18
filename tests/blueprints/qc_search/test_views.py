"""Tests for the views in blueprints/qc_search
"""
import pytest

import tests.utils
from dashboard import models
from dashboard.blueprints.qc_search import views


class TestGetTags:

    def test_tags_are_not_duplicated(self):
        user = models.User.query.get(1)
        tags = views.get_tags(user)
        expected = self.get_tags_from_db()
        assert sorted(tags) == sorted(expected)

    def test_tags_are_sorted(self):
        user = models.User.query.get(1)
        tags = views.get_tags(user)
        expected = self.get_tags_from_db()
        assert tags == sorted(expected)

    def get_tags_from_db(self):
        tags = tests.utils.query_db(
            "SELECT DISTINCT e.scantype"
            "  FROM study_users as su, expected_scans as e"
            "  WHERE su.user_id = 1"
            "    AND su.study = e.study"
            "    AND (su.site = e.site OR su.site IS NULL)"
        )
        return tags


@pytest.fixture(autouse=True)
def records(dash_db):
    """Adds some user records and tags for testing.
    """
    user = models.User("Donald", "Duck")
    dash_db.session.add(user)
    dash_db.session.commit()
    assert user.id == 1

    tests.utils.add_studies({
        "STUDY1": {
            "CMH": ["T1", "T2", "DTI60-1000"]
        },
        "STUDY2": {
            "ABC": ["T1", "ASL", "DTI60-1000"]
        }
    })

    user.add_studies({
        "STUDY1": [],
        "STUDY2": [],
    })
