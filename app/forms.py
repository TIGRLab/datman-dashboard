from datetime import timedelta
from flask_wtf import Form
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.ext.csrf.session import SessionSecureForm
from .models import Study, Site, Session, Scantype, Metrictype

class SecureForm(SessionSecureForm):
    SECRET_KEY = "you will never guess"
    TIME_LIMIT = timedelta(minutes=20)

class SelectMetricsForm(SecureForm):
    study_vals = [(study.id, study.name)
                      for study in Study.query.order_by(Study.name).all()]
    site_vals = [(site.id, site.name)
		      for site in Site.query.order_by(Site.name).all()]
    session_vals = [(session.id, session.name)
		      for session in Session.query.order_by(Session.name).all()]
    scan_vals = [(scan.id, scan.name)
                      for scan in Scan.query.order_by(Scan.name).all()]
    scantype_vals = [(scantype.id, scantype.name)
                      for scantype in Scantype.query.order_by(Scantype.name)]
    metrictype_vals = [(metrictype.id, metrictype.id)
                       for metrictypes in MetricType.query.order_by(Metrictype.name)]


    study_id = SelectField('Study', choices=study_vals, coerce=int)
    site_id = SelectField('Site', choices=site_vals, coerce=int)
    session_id = SelectField('Session', choices=session_vals, coerce=int)
    scan_id = SelectField('Scan', choices=scan_vals, coerce=int)
    scantype_id = SelectField('Scan type', choices=scantype_vals, coerce=int)
    metrictype_id = SelectField('Metric type', choices=metrictype_vals, coerce=int)

    def __init__(self,  *args, **kwargs):
        SecureForm.__init__(self, *args, **kwargs)
        pass
