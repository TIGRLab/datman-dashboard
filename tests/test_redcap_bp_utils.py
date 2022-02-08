import pytest

import dashboard
import dashboard.blueprints.redcap.utils as rc_utils
import datman.scanid


class TestSetSession:

    def test_valid_id_returns_a_dashboard_session_record(self, records):
        name = "STU01_CMH_0001_01_01"
        session = rc_utils.set_session(name)
        assert str(session) == name

    def test_valid_id_with_space_padding_is_accepted(self, records):
        name = " STU01_CMH_0001_01_01 "
        session = rc_utils.set_session(name)
        assert session is not None
        assert str(session) == name.strip()

    def test_id_with_undefined_site_raises_exception(self, dash_db):
        with pytest.raises(dashboard.exceptions.RedcapException):
            rc_utils.set_session("STU01_ABC_0001_01_01")

    def test_id_with_undefined_study_raises_exception(self, dash_db):
        with pytest.raises(dashboard.exceptions.RedcapException):
            rc_utils.set_session("AAA00_CMH_0001_01_01")

    def test_id_with_unexpected_format_raises_exception(self, dash_db):
        with pytest.raises(dashboard.exceptions.RedcapException):
            rc_utils.set_session("STUDYCMH-1000")

    @pytest.fixture
    def records(self, dash_db):
        study = dashboard.models.Study("STUDY1")
        dash_db.session.add(study)
        study.update_site("CMH", code="STU01", create=True)
        return [study]


class TestGetTimepoint:

    def test_can_find_timepoint_by_datman_ident(self, study, ident):
        study.add_timepoint(ident)

        tp = rc_utils.get_timepoint(ident)

        assert tp is not None
        assert tp.name == ident.get_full_subjectid_with_timepoint()
        assert study.id in tp.studies

    def test_creates_timepoint_if_doesnt_exist(self, study, ident):
        tp = rc_utils.get_timepoint(ident)

        assert tp is not None
        assert tp.name == ident.get_full_subjectid_with_timepoint()
        assert study.id in tp.studies

    @pytest.fixture
    def study(self, dash_db):
        study = dashboard.models.Study("STUDY01")
        dash_db.session.add(study)
        study.update_site("CMH", code="STU01", create=True)
        return study

    @pytest.fixture
    def ident(self):
        return datman.scanid.parse("STU01_CMH_0001_01_01")
