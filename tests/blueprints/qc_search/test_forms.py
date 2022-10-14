import dashboard.blueprints.qc_search.forms as forms


class TestGetSearchFormContents:

    def test_excludes_csrftoken_and_submit_fields(self, dash_app):
        with dash_app.test_request_context(
            "/submit-query", method="POST", data={}
        ):
            search_form = forms.QcSearchForm()
            contents = forms.get_search_form_contents(search_form)

        assert "csrf_token" in search_form._fields
        assert "csrf_token" not in contents
        assert "submit" not in contents

    def test_parses_comments_field(self, dash_app):
        data = {"comment": "Corrupted scan;    Truncated"}
        with dash_app.test_request_context(
            "/submit-query", method="POST", data=data
        ):
            search_form = forms.QcSearchForm()
            contents = forms.get_search_form_contents(search_form)

        assert contents["comment"] == ["Corrupted scan", "Truncated"]


class TestParseComment:

    def test_empty_comment_returns_empty_list(self):
        result = forms.parse_comment("")
        assert result == []

    def test_surrounding_whitespace_stripped_from_comments(self):
        expected = ["Corrupted scan"]
        result = forms.parse_comment("\nCorrupted scan")
        assert result == expected

        result = forms.parse_comment("Corrupted scan\t")
        assert result == expected

        result = forms.parse_comment("     Corrupted scan  ")
        assert result == expected

    def test_surrounding_quotes_stripped_from_comments(self):
        expected = ["Corrupted"]
        result = forms.parse_comment("'Corrupted'")
        assert result == expected

        result = forms.parse_comment('"Corrupted"')
        assert result == expected

        result = forms.parse_comment("'Corrupted")
        assert result == expected

    def test_multiple_comments_split_when_semicolon_separator_used(self):
        result = forms.parse_comment("Truncated; Corrupted; bad file")
        assert result == ["Truncated", "Corrupted", "bad file"]
