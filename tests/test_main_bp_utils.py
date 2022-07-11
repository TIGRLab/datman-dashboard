from mock import patch, Mock

import dashboard.blueprints.main.utils as utils


class TestMakeHeaderMsg:

    done_regex = ": Done."
    error_regex = "- ERROR -"

    def test_detects_if_nightly_run_unfinished(self):
        log_contents = """
        Sat 04 Jun 2022 01:08:41 AM EDT: Running pipelines for study: STUDY1
        Sat 04 Jun 2022 01:09:04 AM EDT: Get new scans...
        """
        result = utils.make_header_msg(
            log_contents,
            self.done_regex,
            self.error_regex
        )
        assert result == "Running..."

    def test_counts_errors_in_logs_if_finished(self):
        log_contents = """
        Sat 04 Jun 2022 01:08:41 AM EDT: Running pipelines for study: STUDY1
        Sat 04 Jun 2022 01:09:04 AM EDT: Get new scans...
        2022-06-04 01:46:16,366 - dm_link.py - OPT - ERROR - Scanid not found for archive /archive/data/STUDY1/data/zips/STUDY1_abcd.zip
        2022-06-04 03:40:18,945 - script1.py - STUDY1 - ERROR - Invalid session
        Sat 04 Jun 2022 03:41:40 AM EDT: Done.
        """  # NOQA: E501
        result = utils.make_header_msg(
            log_contents,
            self.done_regex,
            self.error_regex
        )
        assert result == "2 errors reported"

    def test_correct_grammar_when_one_error_exists(self):
        log_contents = """
        Sat 04 Jun 2022 01:08:41 AM EDT: Running pipelines for study: STUDY1
        Sat 04 Jun 2022 01:09:04 AM EDT: Get new scans...
        2022-06-04 03:40:18,945 - script1.py - STUDY1 - ERROR - Invalid session
        Sat 04 Jun 2022 03:41:40 AM EDT: Done.
        """
        result = utils.make_header_msg(
            log_contents,
            self.done_regex,
            self.error_regex
        )
        assert result == "1 error reported"


class TestReadLog:

    @patch("builtins.open")
    def test_escapes_html_present_in_logfile(self, mock_open):
        mock_fh = Mock()
        mock_fh.readlines.return_value = [
            "<textarea> Sometext goes here </textarea>\n",
            "<h3>A header</h3>\n",
            "Sat 04 Jun 2022 01:08:41 AM EDT: Normal log line\n"
        ]
        mock_open.return_value.__enter__.return_value = mock_fh
        result = utils.read_log("/tmp/some_fake_file.txt")

        expected = "&lt;textarea&gt; Sometext goes here &lt;/textarea&gt;" + \
                   "<br><br>&lt;h3&gt;A header&lt;/h3&gt;<br><br>Sat 04 " + \
                   "Jun 2022 01:08:41 AM EDT: Normal log line<br>"
        assert result == expected


class TestGetRunLog:

    @patch("dashboard.blueprints.main.utils.read_log")
    def test_doesnt_try_to_read_file_when_log_dir_not_set(self, mock_read):
        utils.get_run_log("", "STUDY1", ": Done.", "- ERROR -")
        assert mock_read.call_count == 0

    def test_returns_correctly_formatted_dict_when_log_dir_not_set(self):
        result = utils.get_run_log("", "STUDY1", ": Done.", "- ERROR -")
        assert result == {"contents": "", "header": ""}
