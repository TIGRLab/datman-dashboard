import pytest

import dashboard
import dashboard.blueprints.redcap.utils as rc_utils
import datman.scanid


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
