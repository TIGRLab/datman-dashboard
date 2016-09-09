from flask import render_template, flash, url_for, redirect
from app import app
from app.database import db_session
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
    return render_template('getMetricData.html', form=Form)
