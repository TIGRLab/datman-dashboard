import pytest

import dashboard.queries


class TestGetStudies:

    def test_finds_study_by_name(self, records):
        studies = dashboard.queries.get_studies(name="SPINS")
        assert len(studies) == 1
        assert studies[0].id == "SPINS"

    def test_finds_studies_by_tag(self, records):
        studies = dashboard.queries.get_studies(tag="SPN01")
        assert len(studies) == 1
        assert studies[0].id == "SPINS"

    def test_finds_studies_by_scan_site(self, records):
        studies = dashboard.queries.get_studies(site="CMH")
        assert len(studies) == 2

    def test_narrows_search_when_multiple_terms_given(self, records):
        studies = dashboard.queries.get_studies(tag="SPN01", site="CMH")
        assert len(studies) == 1
        assert studies[0].id == "SPINS"

    def test_all_studies_returned_if_no_args_given(self, records):
        studies = dashboard.queries.get_studies()
        assert len(studies) == 3

    def test_create_flag_makes_study_if_doesnt_exist_and_name_is_given(
            self, records):
        studies = dashboard.queries.get_studies("STUDY4", create=True)
        assert len(studies) == 1
        assert studies[0].id == "STUDY4"

    def test_create_flag_ignored_if_no_name_provided(self, records):
        studies = dashboard.queries.get_studies(tag="PRE01", create=True)
        assert not studies

    @pytest.fixture
    def records(self, dash_db):
        study1 = dashboard.models.Study("SPINS")
        dash_db.session.add(study1)

        study1.update_site("CMH", code="SPN01", create=True)
        study1.update_site("UT1", code="SPN01", create=True)
        study1.update_site("MRC", code="SPN02", create=True)

        study2 = dashboard.models.Study("ASCEND")
        dash_db.session.add(study2)

        study2.update_site("CMH", create=True)

        study3 = dashboard.models.Study("ASDD")
        dash_db.session.add(study3)

        dash_db.session.commit()
        return [study1, study2, study3]
