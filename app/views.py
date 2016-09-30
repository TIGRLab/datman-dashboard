from flask import render_template, flash, url_for, redirect, request, jsonify
from app import app
from app.database import db_session
from .queries import query_metric_values_byid
from .models import Study, Site
from .forms import SelectMetricsForm

@app.route('/')
@app.route('/index')
@app.route('/studies')
def index():
    #studies = db_session.query(Study).order_by(Study.nickname).all()
    studies = Study.query.order_by(Study.nickname)
    return render_template('index.html',
                           studies = studies)

@app.route('/sites')
def sites():
    pass

@app.route('/scantypes')
def scantypes():
    pass

@app.route('/study')
@app.route('/study/<int:study_id>', methods=['GET'])
def study(study_id=None):
    if id is not None:
        study = Study.query.get(study_id)
        return render_template('study_details.html',
                                study = study)
    else:
        return redirect('/index')

@app.route('/metricData', methods=['GET','POST'])
def metricData():
    form = SelectMetricsForm()
    if any([form.site_id.data,
            form.study_id.data,
            form.session_id.data,
            form.scan_id.data,
            form.scantype_id.data,
            form.metrictype_id.data]):
        data = query_metric_values_byid(sites = form.site_id.data,
                                        studies = form.study_id.data,
                                        sessions = form.session_id.data,
                                        scans = form.scan_id.data,
                                        scantypes = form.scantype_id.data,
                                        metrictypes = form.metrictype_id.data)
        # assert app.debug==False
    else:
        data=None
    return render_template('getMetricData.html', form=form, data=data)
