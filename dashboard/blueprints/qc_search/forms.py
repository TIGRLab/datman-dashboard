"""Forms and helper functions for use by the qc_search blueprint.
"""

from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, SelectMultipleField, StringField
from wtforms.csrf.core import CSRFTokenField


class QcSearchForm(FlaskForm):
    """Collect search terms to use when looking up QC records.
    """
    approved = BooleanField("Include Approved Scans", default=True)
    blacklisted = BooleanField("Include Blacklisted Scans", default=True)
    flagged = BooleanField("Include Flagged Scans", default=True)
    include_phantoms = BooleanField("Include Phantoms", default=False)
    include_new = BooleanField("Include Scans Without Review", default=False)
    sort = BooleanField("Sort Results", default=False)
    study = SelectMultipleField("Limit to selected studies",
                                render_kw={"class": "qc-search-select"})
    site = SelectMultipleField("Limit to selected sites",
                               render_kw={"class": "qc-search-select"})
    tag = SelectMultipleField("Limit to selected tags",
                              render_kw={"class": "qc-search-select"})
    comment = StringField(
        "Limit to records containing select comments "
        "(use semi-colons to separate multiple comments)",
        render_kw={"class": "qc-search-text"})


def get_search_form_contents(form):
    """Convert the contents of a search form to a dictionary.

    This method will get the contents of a search form, excluding fields like
    csrf_token that only wtforms needs, and parses the contents of fields
    that require modification, and returns the result as a dictionary.

    Args:
        form (wtforms.form.FormMeta): An instance of a WTForm (or FlaskWTForm).

    Returns:
        dict: A dictionary of field names mapped to their value (excludes
            any CSRFToken fields or submit fields).
    """
    contents = {}
    for fname in form._fields:
        field = form._fields[fname]
        if isinstance(field, (CSRFTokenField, SubmitField)):
            continue

        if fname == "comment":
            contents[fname] = parse_comment(field.data)
        else:
            contents[fname] = field.data

    return contents


def parse_comment(user_input):
    """Parse the comment field of a QcSearchForm.

    This will strip extra white space, remove surrounding quotes, and the
    user input by semi-colon.

    Args:
        user_input (str): A semi-colon delimited string of comments to
            parse.

    Returns:
        list: A list of properly formatted strings.
    """
    if not user_input:
        return []

    strip = ['"', "'"]
    search_terms = []
    for term in user_input.split(";"):
        term = term.strip()
        for item in strip:
            term = term.lstrip(item).rstrip(item)
        search_terms.append(term)

    return search_terms
