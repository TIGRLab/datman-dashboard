import os
import logging
import unittest

from mock import Mock, patch, mock_open
from nose.tools import raises

import dashboard.utils as utils
from datman.config import config as Config
import datman.scanid

logging.disable(logging.CRITICAL)

class TestFindMetadata(unittest.TestCase):

    meta_path = "/archive/data/STUDY1/metadata"

    def setUp(self):
        def get_path(path, study):
            if study == "STUDY1":
                return self.meta_path
            raise Exception("Requested config for undefined study")

        mock_config = Mock(spec=Config)
        mock_config.get_path.side_effect = get_path
        utils.CFG = mock_config

    def test_returns_users_file_unmodified_when_given(self):
        provided_file = "/some/path/somewhere/checklist.csv"
        result = utils.find_metadata("checklist.csv", user_file=provided_file)
        assert result == provided_file

    def test_finds_default_file_in_study_metadata_when_no_user_file_given(self):
        expected = os.path.join(self.meta_path, "checklist.csv")
        result = utils.find_metadata("checklist.csv", study="STUDY1")
        assert result == expected

    @raises(Exception)
    def test_raises_exception_when_no_user_file_given_and_cant_locate_default(self):
        result = utils.find_metadata("checklist.csv")
        assert False

class TestGetStudy(unittest.TestCase):

    session = "STU01_CMH_10001_01"
    scan = "STU01_CMH_10001_01_01_T1_02_T1-MPRAGE"
    study = "STUDY1"

    def setUp(self):
        def map_id(name):
            if name == self.session:
                return self.study
            raise ValueError

        mock_config = Mock(spec=Config)
        mock_config.map_xnat_archive_to_project.side_effect = map_id
        utils.CFG = mock_config

    @raises(datman.scanid.ParseException)
    def test_raises_exception_when_malformed_datman_name_given(self):
        malformed_name = "STU01_10001"
        utils.get_study(malformed_name)
        assert False

    @raises(Exception)
    def test_raises_exception_when_cant_identify_study_from_name(self):
        unrecognized_name = "PRE01_CMH_0001_01_01"
        result = utils.get_study(unrecognized_name)
        assert False

    def test_finds_correct_study_from_scan_name(self):
        result = utils.get_study(self.scan)
        assert result == self.study

    def test_finds_correct_study_from_session_name(self):
        result = utils.get_study(self.session)
        assert result == self.study

class GetMetadataEntry(unittest.TestCase):

    qc_match = "qc_STU01_CMP_9999_01.html"
    expected_index = 1
    expected_comment = "AA - approved"

    def setUp(self):
        # Reset this each time, so tests dont modify it and impact each other
        default_checklist = ['qc_STU01_CMH_10001_01.html AA - some comment here\n',
                'qc_STU01_CMP_9999_01.html AA - approved\n',
                'qc_STU01_123456_01.html AA - meh\n']
        self.checklist_contents = default_checklist

    def test_returns_expected_index_when_match_exists(self):
        index, comment = utils.get_metadata_entry(self.checklist_contents,
                self.qc_match)
        assert index == self.expected_index

    def test_returns_expected_comment_when_match_exists(self):
        index, comment = utils.get_metadata_entry(self.checklist_contents,
                self.qc_match)
        assert comment == self.expected_comment

    def test_returns_first_entry_found_that_matches(self):
        duplicate_index = len(self.checklist_contents)
        duplicate_line = "{} ZZ - accidental duplicate sign off here\n"
        self.checklist_contents.append(duplicate_line)

        index, comment = utils.get_metadata_entry(self.checklist_contents,
                self.qc_match)

        assert index != duplicate_index

    def test_returns_correct_values_when_empty_lines_precede_matched_entry(self):
        # Add some white space right before the sought after item to see if
        # it causes an incorrect index to return
        self.checklist_contents.insert(self.expected_index, "\n")
        self.checklist_contents.insert(self.expected_index, "\n")
        expected_index = self.expected_index + 2

        index, comment = utils.get_metadata_entry(self.checklist_contents,
                self.qc_match)

        assert index == expected_index
        assert comment == self.expected_comment

    def test_returned_comment_doesnt_end_in_newline(self):
        bad_comment = self.expected_comment + "\n"

        index, comment = utils.get_metadata_entry(self.checklist_contents,
                self.qc_match)

        assert comment != bad_comment

    def test_returns_index_of_None_when_no_entry_found(self):
        nonexistent_entry = "qc_STU01_UT2_00002_01.html"
        # Make sure it's really not in the checklist contents for the test
        for entry in self.checklist_contents:
            assert nonexistent_entry not in entry

        index, comment = utils.get_metadata_entry(self.checklist_contents,
                nonexistent_entry)

        assert index is None

    def test_returns_empty_string_for_comment_when_no_entry_found(self):
        new_qc_page = "qc_STU01_MRP_00009_01.html"
        # Check it's not in the contents before the real test
        for entry in self.checklist_contents:
            assert new_qc_page not in entry

        index, comment = utils.get_metadata_entry(self.checklist_contents,
                new_qc_page)

        assert comment == ""

@patch("dashboard.utils.find_metadata")
@patch("dashboard.utils.get_contents")
class TestUpdateBlacklist(unittest.TestCase):

    study = "STUDY01"
    blacklist_file = "/some/fake/path/blacklist.csv"
    scan_name = "STU01_UT1_10001_01_01_T1_02_T1-MPRAGE"

    def test_first_line_not_duplicated_when_comment_updated(self,
            mock_get_contents, mock_find_metadata):
        # This test is to prevent a regression - update_blacklist used to
        # just add a whole new line when 'not target_idx', which meant
        # line 0 would be duplicated every time it was updated.

        first_line = "{}\ttruncated scan\n".format(self.scan_name)
        second_line = "some_other_scan\tblacklisted because reasons\n"
        original_contents = [first_line, second_line]

        new_comment = "Not truncated, just because"
        new_line = "{}\t{}\n".format(self.scan_name, new_comment)

        # Set up mocks here
        mock_find_metadata.return_value = self.blacklist_file
        mock_get_contents.return_value = original_contents

        blacklist_mock = mock_open()
        with patch("__builtin__.open", blacklist_mock):
            utils.update_blacklist(self.scan_name, new_comment,
                    study_name=self.study)

        expected_contents = [new_line, second_line]
        blacklist_mock.assert_called_once_with(self.blacklist_file, "w+")
        blacklist_mock().writelines.assert_called_once_with(expected_contents)

    def test_appends_new_line_when_new_scan_is_blacklisted(self,
            mock_get_contents, mock_find_metadata):
        # This test is to prevent a regression where 'existing_comment = None'
        # caused an exception when an entirely new entry was added
        existing_contents = ["some_scan\ttrunacted series\n"]
        comment = "New blacklist entry"
        new_line = "{}\t{}\n".format(self.scan_name, comment)

        mock_find_metadata.return_value = self.blacklist_file
        mock_get_contents.return_value = existing_contents

        blacklist_mock = mock_open()
        with patch("__builtin__.open", blacklist_mock):
            utils.update_blacklist(self.scan_name, comment,
                    study_name=self.study)

        blacklist_mock().write.assert_called_once_with(new_line)

    def test_deleting_scan_not_in_blacklist_does_nothing(self, mock_get_contents,
            mock_find_metadata):
        # Clicking delete multiple times very quickly was causing an
        # exception when 'del lines[None]' tried to run after the first time
        existing_contents = ["some_scan\ttrunacted series\n"]

        mock_find_metadata.return_value = self.blacklist_file
        mock_get_contents.return_value = existing_contents

        blacklist_mock = mock_open()
        with patch("__builtin__.open", blacklist_mock):
            utils.update_blacklist(self.scan_name, None, study_name=self.study)

        assert blacklist_mock().write.call_count == 0
        assert blacklist_mock().writelines.call_count == 0

    def test_removes_entry_when_None_or_empty_string_given_as_comment(self,
            mock_get_contents, mock_find_metadata):

        expected_contents = ["some_scan\tcorrupted file\n"]
        original_contents = [expected_contents[0],
                "{}\tOriginal scan comment\n".format(self.scan_name)]

        mock_find_metadata.return_value = self.blacklist_file
        mock_get_contents.return_value = original_contents

        blacklist_mock = mock_open()
        with patch("__builtin__.open", blacklist_mock):
            utils.update_blacklist(self.scan_name, None, study_name=self.study)

        blacklist_mock().writelines.assert_called_once_with(expected_contents)

@patch("dashboard.utils.find_metadata")
@patch("dashboard.utils.get_contents")
class TestUpdateChecklist(unittest.TestCase):

    study = "STUDY01"
    checklist_file = "/some/fake/path/checklist.csv"
    session = "STU01_UT1_10001_01"

    def test_updates_existing_entry_if_one_exists(self, mock_get_contents,
            mock_find_metadata):
        line_one = "qc_some_session.html some comment here\n"
        original_entry = "qc_{}.html Original comment\n".format(self.session)
        line_three = "qc_another_session.html some comment\n"
        original_contents = [line_one, original_entry, line_three]

        new_comment = "This should replace the old checklist comment"
        expected_contents = [line_one,
                "qc_{}.html {}\n".format(self.session, new_comment),
                line_three]

        mock_find_metadata.return_value = self.checklist_file
        mock_get_contents.return_value = original_contents

        checklist_mock = mock_open()
        with patch("__builtin__.open", checklist_mock):
            utils.update_checklist(self.session, new_comment,
                    study_name=self.study)

        checklist_mock().writelines.assert_called_once_with(expected_contents)

    def test_appends_comment_to_end_of_list_if_new_entry(self, mock_get_contents,
            mock_find_metadata):
        original_contents = ["qc_some_session.html some comment here\n",
                "qc_another_session.html some comment\n"]

        new_comment = "QC'd new session\n"
        new_entry = "qc_{}.html {}\n".format(self.session, new_comment)

        mock_find_metadata.return_value = self.checklist_file
        mock_get_contents.return_value = original_contents

        checklist_mock = mock_open()
        with patch("__builtin__.open", checklist_mock):
            utils.update_checklist(self.session, new_comment,
                    study_name=self.study)

        checklist_mock().write.assert_called_once_with(new_entry)
