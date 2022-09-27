from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, SelectMultipleField, TextField

class QcSearchForm(FlaskForm):
    approved = BooleanField("Include Approved Scans", default=True,
                            render_kw={"class": "qc-search-bool"})
    blacklisted = BooleanField("Include Blacklisted Scans", default=True,
                               render_kw={"class": "qc-search-bool"})
    flagged = BooleanField("Include Flagged Scans", default=True,
                           render_kw={"class": "qc-search-bool"})
    include_phantoms = BooleanField("Include Phantoms", default=False,
                                    render_kw={"class": "qc-search-bool"})
    include_new = BooleanField("Include Scans Without Review", default=False,
                               render_kw={"class": "qc-search-bool"})
    study = SelectMultipleField("Select all studies to search",
                                render_kw={"class": "qc-search-select"})
    site = SelectMultipleField("Select all sites to search",
                               render_kw={"class": "qc-search-select"})
    tag = SelectMultipleField("Select all tags to search",
                              render_kw={"class": "qc-search-select"})
    comment = TextField(
        "Enter a semi-colon delimited list of comments to search for",
        render_kw={"class": "qc-search-text"})

    submit = SubmitField("Search")
