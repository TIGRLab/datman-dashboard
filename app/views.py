from flask import render_template, flash, url_for, redirect, request, jsonify
from app import app
from .queries import query_metric_values_byid, query_metric_types
from .models import Study, Site
from .forms import SelectMetricsForm
import json


@app.route('/')
@app.route('/index')
@app.route('/studies')
def index():
    # studies = db_session.query(Study).order_by(Study.nickname).all()
    studies = Study.query.order_by(Study.nickname)
    return render_template('index.html',
                           studies=studies)


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
                               study=study)
    else:
        return redirect('/index')


@app.route('/metricData', methods=['GET', 'POST'])
def metricData():
    form = SelectMetricsForm()
    data = None
    # Need to add a query_complete flag to the form

    if form.query_complete.data == 'True':
        data = metricDataAsJson()

    if any([form.study_id.data,
            form.site_id.data,
            form.scantype_id.data,
            form.metrictype_id.data]):
        form_vals = query_metric_types(studies=form.study_id.data,
                                       sites=form.site_id.data,
                                       scantypes=form.scantype_id.data,
                                       metrictypes=form.metrictype_id.data)
    else:
        form_vals = query_metric_types()

    study_vals = []
    site_vals = []
    scantype_vals = []
    metrictype_vals = []

    for res in form_vals:
        study_vals.append((res[0].id, res[0].name))
        site_vals.append((res[1].id, res[1].name))
        scantype_vals.append((res[2].id, res[2].name))
        metrictype_vals.append((res[3].id, res[3].name))
        # study_vals.append((res.id, res.name))
        # for site in res.sites:
        #     site_vals.append((site.id, site.name))
        # for scantype in res.scantypes:
        #     scantype_vals.append((scantype.id, scantype.name))
        #     for metrictype in scantype.metrictypes:
        #         metrictype_vals.append((metrictype.id, metrictype.name))

    #sort the values alphabetically
    study_vals = sorted(set(study_vals), key=lambda v: v[1])
    site_vals = sorted(set(site_vals), key=lambda v: v[1])
    scantype_vals = sorted(set(scantype_vals), key=lambda v: v[1])
    metrictype_vals = sorted(set(metrictype_vals), key=lambda v: v[1])

    form.study_id.choices = study_vals
    form.site_id.choices = site_vals
    form.scantype_id.choices = scantype_vals
    form.metrictype_id.choices = metrictype_vals

    return render_template('getMetricData.html', form=form, data=data)


def _checkRequest(request, key):
    # Checks a post request, returns none if key doesn't exist
    try:
        return(request.form.getlist(key))
    except KeyError:
        return(None)


@app.route('/metricDataAsJson', methods=['Get', 'Post'])
def metricDataAsJson(format='plain'):
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
        metricValue = m
        objects.append({'value':            metricValue.value,
                        'metrictype':       metricValue.metrictype.name,
                        'metrictype_id':    metricValue.metrictype_id,
                        'scan_id':          metricValue.scan_id,
                        'scan_name':        metricValue.scan.name,
                        'scantype':         metricValue.scan.scantype.name,
                        'scantype_id':      metricValue.scan.scantype_id,
                        'session_id':       metricValue.scan.session_id,
                        'session_name':     metricValue.scan.session.name,
                        'session_date':     metricValue.scan.session.date,
                        'site_id':          metricValue.scan.session.site_id,
                        'site_name':        metricValue.scan.session.site.name,
                        'study_id':         metricValue.scan.session.study_id,
                        'study_name':       metricValue.scan.session.study.name})
    if format == 'http':
        return(jsonify(objects))
    else:
        return(json.dumps(objects, indent=4, separators=(',', ': ')))
