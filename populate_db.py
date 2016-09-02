from app.database import db_session
from app.models import Study, Site, Session, Scan, ScanType, MetricType, MetricValue
import numpy as np
import random, datetime

"""Populate the database with some sample data"""

def gen_random_date():
        oldest = 364 * 5
        d = datetime.timedelta(days = oldest * np.random.random())
        return(datetime.date.today() - d)

def create_random_metricvalue(metrictype):
    """Create a random value based on the metrictype"""

    # define a dict with distributions of values
    metrictypes = {'SNR': (50, 10),
                   'Movement': (0.5, 1)}
    return(np.random.normal(metrictypes[metrictype][0],
                       metrictypes[metrictype][1]))


def create_random_session(study_str, session_id):
    """Creates a random testing session for a study
    study is identified by its nickname string
    session_id is a string used to ensure the session name is unique"""
    # get the study from the database
    study = Study.query.filter(Study.nickname == study_str).first()
    #pick a random site
    site = study.sites[np.random.randint(len(study.sites))]
    #create a random Date
    session_date = gen_random_date()
    #create a Session
    session = Session()
    session.name = '{}_{}_{}_{}'.format(study.name, site.name, session_date, session_id)
    session.date = session_date
    session.site = site
    study.sessions.append(session)

    for scantype in study.scantypes:
        #create a new scan
        scan = Scan()
        scan.name = '{}_{}'.format(session.name, scantype.name)
        scan.scantype = scantype
        session.scans.append(scan)
        for metrictype in scantype.metrictypes:
            newval = create_random_metricvalue(metrictype.name)
            metricvalue = MetricValue()
            metricvalue.metrictype = metrictype
            metricvalue.value = newval
            scan.metricvalues.append(metricvalue)
    db_session.add(s)


if __name__ == '__main__':
    # first we populate the objects (studies, sites, scantypes etc.)
    # create some sample sites
    sample_sites = ['Site1', 'Site2', 'Site3']
    sites_obj = []
    for site_name in sample_sites:
        s = Site()
        s.name = site_name
        db_session.add(s)
        sites_obj.append(s)

    # some sample metrictypes
    sample_metrics = ['SNR', 'Movement']

    # some sample scantypes
    sample_scantypes = [{'name': 'T1', 'metrics': [sample_metrics[0], sample_metrics[1]]},
                        {'name': 'T2', 'metrics': [sample_metrics[0]]},
                        {'name': 'DTI', 'metrics': [sample_metrics[1]]},
                        {'name': 'FMRI', 'metrics': []}]

    scantypes_obj = []
    for scantype in sample_scantypes:
        s = ScanType()
        s.name = scantype['name']
        for metrictype in scantype['metrics']:
            new_metric = MetricType(name=metrictype)
            s.metrictypes.append(new_metric)
        db_session.add(s)
        scantypes_obj.append(s)

    # some sample studies, one study has two sites, site3 isn't used
    sample_studies = [{'nickname': 'study1', 'name': 'Study 1',
                       'sites': [sites_obj[0]],
                       'scantypes': [scantypes_obj[0], scantypes_obj[1]]},
                      {'nickname': 'study2', 'name': 'Study 2',
                       'sites': [sites_obj[1]],
                       'scantypes': [scantypes_obj[0], scantypes_obj[2]]},
                      {'nickname': 'study3', 'name': 'Study 3',
                       'sites': [sites_obj[0], sites_obj[1]],
                       'scantypes': [scantypes_obj[0], scantypes_obj[1], scantypes_obj[3]]}]
    study_obj = []
    for study in sample_studies:
        s = Study(nickname=study['nickname'],
                  name=study['name'])

        for site in study['sites']:
            s.sites.append(site)

        for scantype in study['scantypes']:
            s.scantypes.append(scantype)

        db_session.add(s)
        db_session.commit()

    # now generate some 'real' sessions
    random.seed(1234)
    for i in range(1000):
        #pick a random study name
        random_study_name = sample_studies[random.randrange(len(sample_studies))]['nickname']
        create_random_session(random_study_name, i)
        db_session.commit()
