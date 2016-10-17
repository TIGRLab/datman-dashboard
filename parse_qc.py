import pandas as pd
import os
import sys
import datman as dm
#db_path = "/projects/twright/dashboard"
#if db_path not in sys.path:
#	sys.path.append("/projects/twright/dashboard")
print sys.path

from app import db
from app.models import Study, Site, Session, Scan, ScanType, MetricType, MetricValue

root_dir = "/archive/data/"

def read_qc(path_to_file, space_delimited):
	return pd.read_csv(path_to_file, delim_whitespace=space_delimited, header=None).as_matrix()

def insert(df, df_path):

	recognized_files = ("_stats.csv", "_scanlengths.csv", "_qascript_fmri.csv", "_qascript_dti.csv")
	if not df.endswith(recognized_files):
		#print "Unrecognized .csv file in subject folder; skipping."
		return

	sep_df = df.split("_")
	if sep_df[2] == "PHA":
		proj_name, site_name, subj_name, tag = sep_df[0], sep_df[1], sep_df[2] + "_" + sep_df[3], sep_df[4]
	else:
		proj_name, site_name, subj_name, tag = sep_df[0], sep_df[1], sep_df[2], sep_df[5]

	study_name = dm.config.map_xnat_archive_to_project(proj_name)

	if Study.query.filter(Study.nickname == study_name).count():
		study = Study.query.filter(Study.nickname == study_name).first()
		#print "Using existing record."
	else:
		print "Study (" + study_name + ") does not exist in database; skipping."
		return

	session_name = proj_name + "_" + site_name + "_" + subj_name

	if Session.query.filter(Session.name == session_name).count():
		session = Session.query.filter(Session.name == session_name).first()
		#print "Using existing record."
	else:
		session = Session()
		session.name = session_name
		#db_session.add(session)
	study.sessions.append(session)

	possible_sites = study.sites

	for site in possible_sites:
		#print site.name
		if site.name == site_name:
			session.site = site

	if not session.site:
		print "Site (" + site_name + ") not associated with study " + proj_name + " in database; skipping."
		return

	scan_name = session_name + "_" + tag

	if Scan.query.filter(Scan.name == scan_name).count():
		scan = Scan.query.filter(Scan.name == scan_name).first()
		#print "Using existing record."
	else:
		scan = Scan()
		scan.name = scan_name
		#db_session.add(scan)
	session.scans.append(scan)

	possible_scantypes = study.scantypes

	for scantype in possible_scantypes:
		#print scantype.name
		if scantype.name == tag:
			scan.scantype = scantype

	if not scan.scantype:
		print "Scantype (" + tag + ") not associated with study " + proj_name + " in database; skipping."
		return

	if df.endswith("_stats.csv"):
		#print "stats.csv file"
		try:
			data = read_qc(df_path, False)
			zipped_data = zip(data[0],data[1])
			for datapoint in zipped_data:
				metricvalue = MetricValue()
				if MetricType.query.filter(MetricType.name == datapoint[0]).count() and MetricType.query.filter(MetricType.scantype_id == scan.scantype_id).count():
					metrictype = MetricType.query.filter(MetricType.name == datapoint[0]).filter(MetricType.scantype_id == scan.scantype_id).first()
					print "Using existing record."
				else:
					metrictype = MetricType()
					metrictype.name = datapoint[0]
					metrictype.scantype_id = scan.scantype_id
				metricvalue.metrictype = metrictype
				metricvalue.value = datapoint[1]
				scan.metricvalues.append(metricvalue)
		except (IndexError, ValueError):
			print df + " missing data"

	elif df.endswith("_scanlengths.csv"):
		#print "scanlengths.csv file"
		try:
			data = read_qc(df_path, False)
			metricvalue = MetricValue()
			if MetricType.query.filter(MetricType.name == "ScanLength").count() and MetricType.query.filter(MetricType.scantype_id == scan.scantype_id).count():
				metrictype = MetricType.query.filter(MetricType.name == "ScanLength").filter(MetricType.scantype_id == scan.scantype_id).first()
					#print "Using existing record."
			else:
				metrictype = MetricType()
				metrictype.name = "ScanLength"
				metrictype.scantype_id = scan.scantype_id
			metricvalue.metrictype = metrictype
			metricvalue.value = data[0][1]
			scan.metricvalues.append(metricvalue)
		except (IndexError, ValueError):
			#print "Metric file (" + df + ") is missing data or not formatted correctly; skipping."
			print df + " missing data"

	elif df.endswith("_qascript_fmri.csv") or df.endswith("_qascript_dti.csv"):
		#print "qascript_*.csv file"
		try:
			data = read_qc(df_path, True)
			for datapoint in data:
				metricvalue = MetricValue()
				if MetricType.query.filter(MetricType.name == datapoint[0]).count() and MetricType.query.filter(MetricType.scantype_id == scan.scantype_id).count():
					metrictype = MetricType.query.filter(MetricType.name == datapoint[0]).filter(MetricType.scantype_id == scan.scantype_id).first()
					#print "Using existing record."
				else:
					metrictype = MetricType()
					metrictype.name = datapoint[0]
					metrictype.scantype_id = scan.scantype_id
				metricvalue.metrictype = metrictype
				metricvalue.value = datapoint[1]
				scan.metricvalues.append(metricvalue)
		except (IndexError, ValueError):
			#print "Metric file (" + df + ") is missing data or not formatted correctly; skipping."
			print df + " missing data"

	db.session.commit()

def traverse_projects():
	#Ignore these files in "data" folder
	#exclusions = ["assets", "code", "UNITTEST", "README.md", "WEBSITE", "logs", "data-env", ".jobscript", ".RData"]
	#exclusions = ["STOPPD", "DBDC", "RTMSWM", "PASD", "COGBDY", "VIPR", "DTI3T", "DTI15T", "PACTMD", "COGBDO", "SPINS", "code", "README.md"]
	exclusions = ["code", "README.md"]
	projects = os.listdir(root_dir)
	projects = filter(lambda dir: dir not in exclusions, projects)

	for project in projects:
		qc_dir = root_dir + project + "/qc/"
		if os.path.isdir(qc_dir):
			#Ignore these files in a project's "qc" folder
			exclusions = ["subject-qc.db", "checklist.csv", "logs", "phantom", "papaya.js", "papaya.css", "index.html"]
			subjects = os.listdir(qc_dir)
			subjects = filter(lambda dir: dir not in exclusions, subjects)

			for subject in subjects:
				subj_dir = qc_dir + subject
				#List all .csv files in a subject folder
				datafiles = filter(lambda file: file.endswith(".csv"), os.listdir(subj_dir))
				for df in datafiles:
					df_path = subj_dir + "/" + df
					print df
					insert(df, df_path)

traverse_projects()
