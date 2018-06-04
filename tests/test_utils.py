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
