#!venv/bin/python
"""
Add extra study information into the database.
Parses the datman config files for study information and updates
    information in the database.

usage:
$ source activate /archive/code/dashboard/venv/bin/activate
$ module load /archive/code/datman_env.module
$ module load /archive/code/dashboard.module
$ add_study_info.py
"""

from dashboard import db
from dashboard.models import Study, Person, Site, ScanType
import datman as dm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    cfg = dm.config.config()
    for key in cfg.site_config['Projects'].keys():
        logger.info('Getting settings for study:{}'.format(key))
        cfg.set_study(key)
        # get the study from the db if it exists, create if not
        if Study.query.filter(Study.nickname == key).count():
            logger.debug('Getting study:{} from database'.format(key))
            study = Study.query.filter(Study.nickname == key).first()
        else:
            logger.debug('Creating study:{}'.format(key))
            study = Study()
            study.nickname = key
            db.session.add(study)

        # populate db fields from the yaml files
        fullname = cfg.get_if_exists('study', ['FullName'])
        description = cfg.get_if_exists('study', ['Description'])
        if fullname:
            study.name = fullname
        if description:
            study.description = description

        contact_name = cfg.get_if_exists('study', ['PrimaryContact'])
        #Get the primary contact information
        if not contact_name:
            logger.warning('Contact not set for study:{}.format(key)')
        else:
            if Person.query.filter(Person.name == contact_name).count():
                logger.debug('Getting person:{} from database'
                             .format(contact_name))
                contact = Person.query.filter(Person.name == contact_name).first()
            else:
                logger.debug('Creating person:{}'.format(contact_name))
                contact = Person()
                contact.name = contact_name
                db.session.add(contact)

            study.primary_contact = contact

        sites = cfg.get_if_exists('study', ['Sites'])
        if not sites:
            logger.error('Sites not found for study:{}'.format(key))
            continue

        all_scan_types = []
        for site_name in sites.keys():
            # build a list of potential scantypes for each study while we
            # loop through the study sites
            scan_types = cfg.get_if_exists('study',
                                           ['Sites', site_name, 'ExportInfo'])
            if not scan_types:
                logger.warning('ScanTypes not found for Study:{} at site:{}'
                               .format(key, site_name))
                continue
            all_scan_types = all_scan_types + scan_types.keys()

            # deal with type PDT2 which is split into PD & T2
            if 'PDT2' in all_scan_types:
                all_scan_types.append('PD')
                all_scan_types.append('T2')

            # get site from db or create and append to study
            if Site.query.filter(Site.name == site_name).count():
                logger.debug('Getting site:{} from database'.format(site_name))
                site = Site.query.filter(Site.name == site_name).first()
            else:
                logger.debug('Creating site:{}')
                site = Site()
                site.name = site_name
                db.session.add(site)

            study.sites.append(site)

        #now process the scan types
        all_scan_types = set(all_scan_types)
        for scan_type_name in all_scan_types:
            if ScanType.query.filter(ScanType.name == scan_type_name).count():
                logger.debug('Getting scantype:{} from database'
                             .format(scan_type_name))
                scan_type = ScanType \
                    .query \
                    .filter(ScanType.name == scan_type_name).first()
            else:
                logger.debug('Creating scantype:{}'.format(scan_type_name))
                scan_type = ScanType()
                scan_type.name = scan_type_name
                db.session.add(scan_type)

            study.scantypes.append(scan_type)

        db.session.commit()


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    main()
