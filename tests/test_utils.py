import unittest
import dashboard.utils as utils

class TestUpdateBlacklist(unittest.TestCase):

    def test_first_line_not_duplicated_when_comment_updated(self):
        # This test is to prevent a regression - update_blacklist used to
        # just add a whole new line when 'not target_idx', which meant
        # line 0 would be duplicated every time it was updated.
        assert False

    def test_appends_new_line_when_new_scan_is_blacklisted(self):
        # To prevent a regression where 'existing_comment = None' caused
        # an exception when an entirely new entry was added
        assert False

    def test_removes_entry_when_None_or_empty_string_given_as_comment(self):
        assert False

    def test_updates_existing_entry_when_scan_name_is_already_blacklisted(self):
        assert False

    def test_updates_first_entry_when_scan_name_is_duplicated_in_list(self):
        assert False

class TestUpdateChecklist(unittest.TestCase):

    def test_updates_existing_entry_if_one_exists(self):
        assert False

    def test_appends_comment_to_end_of_list_if_new_entry(self):
        assert False

class TestFindMetadata(unittest.TestCase):

    def test_returns_users_file_unmodified_when_given(self):
        assert False

    def test_finds_default_file_in_study_metadata_when_no_user_file_given(self):
        assert False

    def test_raises_exception_when_no_user_file_given_and_cant_locate_default(self):
        assert False

class TestGetStudy(unittest.TestCase):

    def test_raises_exception_when_malformed_datman_name_given(self):
        assert False

    def test_raises_exception_when_cant_identify_study_from_name(self):
        assert False

    def test_finds_correct_study_from_scan_name(self):
        assert False

    def test_finds_correct_study_from_session_name(self):
        assert False

class GetMetadataEntry(unittest.TestCase):

    def test_returns_first_entry_found_that_matches(self):
        assert False

    def test_returns_expected_index_when_match_exists(self):
        assert False

    def test_returns_expected_comment_when_match_exists(self):
        assert False

    def test_ignores_empty_lines(self):
        assert False

    def test_returns_index_of_None_when_no_entry_found(self):
        assert False

    def test_returns_empty_comment_when_no_entry_found(self):
        assert False

    def test_comment_doesnt_end_in_newline(self):
        assert False
