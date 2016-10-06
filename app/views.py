from flask import render_template, flash, url_for, redirect, request, jsonify
from app import app
from app.database import db_session
from .queries import query_metric_values_byid
from .models import Study, Site
from .forms import SelectMetricsForm
import json

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
        #data = query_metric_values_byid(sites = form.site_id.data,
        #                                studies = form.study_id.data,
        #                                sessions = form.session_id.data,
        #                                scans = form.scan_id.data,
        #                                scantypes = form.scantype_id.data,
        #                                metrictypes = form.metrictype_id.data)
        # assert app.debug==False

        data = metricDataAsJson(format='plain')
    else:
        data=None
    return render_template('getMetricData.html', form=form, data=data)

def _checkRequest(request, key):
    # Checks a post request, returns none if key doesn't exist
    try:
        return(request.form.getlist(key))
    except KeyError:
        return(None)

@app.route('/metricDataAsJson', methods=['Get','Post'])
def metricDataAsJson(format='http'):
    fields = {'studies': 'study_id',
              'sites': 'site_id',
              'sessions': 'session_id',
              'scans': 'scan_id',
              'scantypes': 'scantype_id',
              'metrictypes': 'metrictype_id'}

    for k, v in fields.iteritems():
        if request.method == 'POST':
            fields[k] = _checkRequest(request, v)

        else:
            if request.args.get(v):
                fields[k] = request.args.get(v).split(',')
            else:
                fields[k] = request.args.get(v)

    # remove None values from the dict
    fields = dict((k, v) for k, v in fields.iteritems() if v)
    # convert from strings to integers
    for k, vals in fields.iteritems():
        try:
            fields[k] = int(vals)
        except TypeError:
            fields[k] = [int(v) for v in vals]

    data = query_metric_values_byid(**fields)
    objects = []
    for m in data:
        objects.append({'value':m.value,
                        'metrictype':    m.metrictype.name,
                        'metrictype_id': m.metrictype_id,
                        'scan_id':       m.scan_id,
                        'scan_name':     m.scan.name,
                        'scantype':     m.scan.scantype.name,
                        'scantype_id':  m.scan.scantype_id,
                        'session_id':    m.scan.session_id,
                        'session_name':  m.scan.session.name,
                        'session_date':  m.scan.session.date,
                        'site_id':       m.scan.session.site_id,
                        'site_name':     m.scan.session.site.name,
                        'study_id':      m.scan.session.study_id,
                        'study_name':    m.scan.session.study.name})
    if format == 'http':
        return(jsonify(objects))
    else:
        return(json.dumps(objects, indent=4, separators=(',',': ')))
