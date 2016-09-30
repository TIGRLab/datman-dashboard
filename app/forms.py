from datetime import timedelta
from flask import session
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from .models import Study, Site, Scan, Session, ScanType, MetricType

from wtforms.csrf.session import SessionCSRF

class SelectMetricsForm(FlaskForm):
    study_vals = [(study.id, study.name)
                      for study in Study.query.order_by(Study.name).all()]
    study_vals = [(0, 'Select')] + study_vals
    site_vals = [(site.id, site.name)
		      for site in Site.query.order_by(Site.name).all()]
    site_vals = [(0, 'Select')] + site_vals
    session_vals = [(session.id, session.name)
		      for session in Session.query.order_by(Session.name).all()]
    session_vals = [(0, 'Select')] + session_vals
    scan_vals = [(scan.id, scan.name)
                      for scan in Scan.query.order_by(Scan.name).all()]
    scan_vals = [(0, 'Select')] + scan_vals
    scantype_vals = [(scantype.id, scantype.name)
                      for scantype in ScanType.query.order_by(ScanType.name)]
    scantype_vals = [(0, 'Select')] + scantype_vals
    metrictype_vals = [(metrictype.id, metrictype.name)
                       for metrictype in MetricType.query.order_by(MetricType.name)]
    metrictype_vals = [(0, 'Select')] + metrictype_vals

    study_id      = SelectMultipleField('Study', choices=study_vals, coerce=int)
    site_id       = SelectMultipleField('Site', choices=site_vals, coerce=int)
    session_id    = SelectMultipleField('Session', choices=session_vals, coerce=int)
    scan_id       = SelectMultipleField('Scan', choices=scan_vals, coerce=int)
    scantype_id   = SelectMultipleField('Scan type', choices=scantype_vals, coerce=int)
    metrictype_id = SelectMultipleField('Metric type', choices=metrictype_vals, coerce=int)

    def __init__(self,  *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
