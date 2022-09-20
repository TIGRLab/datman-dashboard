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

    def test_find_studies_can_locate_by_alt_study_code(self, records):
        alt_code = dashboard.models.AltStudyCode()
        alt_code.study_id = "SPINS"
        alt_code.site_id = "UT1"
        alt_code.code = "SPN02"
        dashboard.models.db.session.add(alt_code)
        dashboard.models.db.session.commit()

        studies = dashboard.queries.get_studies(tag="SPN02")
        assert len(studies) == 1
        assert studies[0].id == "SPINS"

    @pytest.fixture
    def records(self, dash_db):
        study1 = dashboard.models.Study("SPINS")
        dash_db.session.add(study1)

        study1.update_site("CMH", code="SPN01", create=True)
        study1.update_site("UT1", code="SPN01", create=True)

        study2 = dashboard.models.Study("ASCEND")
        dash_db.session.add(study2)

        study2.update_site("CMH", create=True)

        study3 = dashboard.models.Study("ASDD")
        dash_db.session.add(study3)

        dash_db.session.commit()
        return [study1, study2, study3]


class TestGetScanQc:

    qc_entries = {
        "approved": [
            "STUDY1_CMH_0001_01_01_T1_10",
            "STUDY2_CMH_4444_01_01_T2_04"
        ],
        "blacklisted": [
            "STUDY1_UTO_0002_01_01_T1_10",
            "STUDY2_CMH_4444_01_01_T2_03"
        ],
        "flagged": ["STUDY1_CMH_0001_01_01_DTI60-1000_11"],
        "new": ["STUDY2_CMH_4444_01_01_RST_05"],
        "approved_phantom": ["STUDY1_CMH_PHA_FBN190428_T1_01"],
        "blacklist_phantom": ["STUDY2_CMH_PHA_FBN220920_T2_01"]
    }

    def assert_all_entries_found(self, found, expected):
        """Raises AssertionError if any 'expected' scans missing from 'found'.
        """
        scan_list = [item[0] for item in found]
        for scan in expected:
            assert scan in scan_list

    def test_finds_all_reviewed_scans_when_no_search_terms(self):
        result = dashboard.queries.get_scan_qc()

        expected = []
        expected.extend(self.qc_entries["approved"])
        expected.extend(self.qc_entries["flagged"])
        expected.extend(self.qc_entries["blacklisted"])

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_finds_all_except_approved_when_flag_is_false(self):
        result = dashboard.queries.get_scan_qc(approved=False)

        expected = []
        expected.extend(self.qc_entries["flagged"])
        expected.extend(self.qc_entries["blacklisted"])

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_finds_all_except_flagged_when_flag_is_false(self):
        result = dashboard.queries.get_scan_qc(flagged=False)

        expected = []
        expected.extend(self.qc_entries["approved"])
        expected.extend(self.qc_entries["blacklisted"])

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_finds_all_except_blacklisted_when_flag_is_false(self):
        result = dashboard.queries.get_scan_qc(blacklisted=False)

        expected = []
        expected.extend(self.qc_entries["approved"])
        expected.extend(self.qc_entries["flagged"])

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_can_return_only_approved_entries(self):
        result = dashboard.queries.get_scan_qc(
            blacklisted=False, flagged=False)
        expected = self.qc_entries["approved"]

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_can_return_only_flagged_entries(self):
        result = dashboard.queries.get_scan_qc(
            approved=False, blacklisted=False)
        expected = self.qc_entries["flagged"]

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    def test_can_return_only_blacklisted_entries(self):
        result = dashboard.queries.get_scan_qc(
            approved=False, flagged=False)
        expected = self.qc_entries["blacklisted"]

        assert len(result) == len(expected)
        self.assert_all_entries_found(result, expected)

    ##### Need to test combinations of options (sigh)
    # approve = False, plus phantoms
    # approve = False, plus new
    # approve = False, flagged = False
    # etc... All combinations for (approve, flag, blacklist) and (new, phantom)

    # def test_finds_all_qc_matching_study(self, records):
    #     assert False

    # def test_finds_all_qc_matching_studies(self, records):
    #     assert False
    #
    # def test_finds_all_qc_matching_author(self, records):
    #     assert False
    #
    # def test_finds_all_qc_matching_authors(self, records):
    #     assert False
    #
    # def test_finds_all_qc_matching_tag(self, records):
    #     assert False
    #
    # def test_finds_all_qc_matching_tags(self, records):
    #     assert False
    #

    #
    # def test_finds_flagged_scans(self, records):
    #     assert False
    #
    # def test_finds_blacklisted_scans(self, records):
    #     assert False
    #
    # def test_finds_unreviewed_scans_when_user_sets_all_flags_to_false(
    #         self, records):
    #     assert False
    #
    # def test_finds_entries_matching_comment(self, records):
    #     assert False

    @pytest.fixture(autouse=True, scope="class")
    def records(self, read_only_db):
        """Create checklist entries to search.

        The end result should be the following QC review data available to be
        searched by tests:

        ===================================  ======== ========== ========
        Scan                                 Reviewer Status     Comment
        ===================================  ======== ========== ========
        STUDY1_CMH_0001_01_01_T1_10          1        approve
        STUDY1_CMH_0001_01_01_DTI60-1000_11  1        flag       meh
        STUDY1_UTO_0002_01_01_T1_10          2        blacklist  bad scan
        STUDY1_CMH_PHA_FBN190428_T1_01       1        approve
        STUDY2_CMH_4444_01_01_T2_03          1        blacklist  corrupted
        STUDY2_CMH_4444_01_01_T2_04          2        approve
        STUDY2_CMH_4444_01_01_RST_05
        STUDY2_CMH_PHA_FBN220920_T2_01       2        blacklist  corrupted
        """
        user1 = dashboard.models.User('Jane', 'Doe')
        user2 = dashboard.models.User('John', 'Doe')
        read_only_db.session.add(user1)
        read_only_db.session.add(user2)

        read_only_db.session.add(dashboard.models.Scantype("T1"))
        read_only_db.session.add(dashboard.models.Scantype("T2"))
        read_only_db.session.add(dashboard.models.Scantype("DTI60-1000"))
        read_only_db.session.add(dashboard.models.Scantype("RST"))

        # Add the first study and mock data
        study1 = dashboard.models.Study('STUDY1')
        read_only_db.session.add(study1)
        study1.update_site("CMH", create=True)
        study1.update_site("UTO", create=True)
        study1.update_scantype("CMH", "T1", create=True)
        study1.update_scantype("CMH", "DTI60-1000", create=True)
        study1.update_scantype("UTO", "T1", create=True)

        tp1 = dashboard.models.Timepoint("STUDY1_CMH_0001_01", "CMH")
        study1.add_timepoint(tp1)
        tp1.add_session(1)
        scan1 = tp1.sessions[1].add_scan(
            "STUDY1_CMH_0001_01_01_T1_10", 10, "T1")
        scan1.add_checklist_entry(user1.id, sign_off=True)
        scan2 = tp1.sessions[1].add_scan(
            "STUDY1_CMH_0001_01_01_DTI60-1000_11", 11, "DTI60-1000")
        scan2.add_checklist_entry(user1.id, comment="meh",
                                  sign_off=True)

        tp2 = dashboard.models.Timepoint("STUDY1_UTO_0002_01", "UTO")
        study1.add_timepoint(tp2)
        tp2.add_session(1)
        scan3 = tp1.sessions[1].add_scan(
            "STUDY1_UTO_0002_01_01_T1_10", 10, "T1")
        scan3.add_checklist_entry(user2.id, comment="bad scan", sign_off=False)

        tp3 = dashboard.models.Timepoint("STUDY1_CMH_PHA_FBN190428", "CMH",
                                         is_phantom=True)
        study1.add_timepoint(tp3)
        tp3.add_session(1)
        scan4 = tp3.sessions[1].add_scan(
            "STUDY1_CMH_PHA_FBN190428_T1_01", 1, "T1")
        scan4.add_checklist_entry(user1.id, sign_off=True)

        # Add the second study and mock data
        study2 = dashboard.models.Study('STUDY2')
        read_only_db.session.add(study2)
        study2.update_site("CMH", create=True)
        study2.update_scantype("CMH", "T2", create=True)
        study2.update_scantype("CMH", "RST", create=True)

        tp4 = dashboard.models.Timepoint("STUDY2_CMH_4444_01", "CMH")
        study2.add_timepoint(tp4)
        tp4.add_session(1)
        scan5 = tp4.sessions[1].add_scan(
            "STUDY2_CMH_4444_01_01_T2_03", 3, "T2"
        )
        scan5.add_checklist_entry(
            user1.id, sign_off=False, comment="corrupted")
        scan6 = tp4.sessions[1].add_scan(
            "STUDY2_CMH_4444_01_01_T2_04", 4, "T2")
        scan6.add_checklist_entry(user2.id, sign_off=True)
        scan7 = tp4.sessions[1].add_scan(
            "STUDY2_CMH_4444_01_01_RST_05", 5, "RST")

        tp5 = dashboard.models.Timepoint(
            "STUDY2_CMH_PHA_FBN220920", "CMH", is_phantom=True)
        study2.add_timepoint(tp5)
        tp5.add_session(1)
        scan8 = tp5.sessions[1].add_scan(
            "STUDY2_CMH_PHA_FBN220920_T2_01", 1, "T2")
        scan8.add_checklist_entry(
            user2.id, sign_off=False, comment="corrupted")

        return read_only_db
