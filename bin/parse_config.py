#!/usr/bin/env python
"""Update the dashboard's configuration based on Datman's config yaml files.

This script should be run by a user with permission to update the dashboard's
database.

Any new studies that are found will be added to the database and existing
studies are updated to match the config files wherever the database differs.
The user is also given the option to delete any records (tags, studies, sites)
that aren't found in the config files. Be warned: these deletes will cascade to
scans that reference the bad values (e.g. deleting a tag that's no longer used
for a study, like 'FMAP', will also delete all scan records for that study with
that tag).

To prevent a project's settings file from being added to the database
add the key 'DB_IGNORE', with any value other than the boolean False, to
the settings file.

Usage:
    parse_config.py [options]
    parse_config.py [options] <study>

Args:
    <study>         Only update the configuration for the given study. Note
                    that this will cause errors if a tag is entirely new
                    (i.e. the global configuration must define a tag before
                    a study can reference it).
Options:
    --accept        Automatically answer 'y' to all prompts. Use with caution:
                    Deletes for studies + tags will purge associated
                    scan / timepoint / session records and updates may
                    overwrite newer information in the database if the
                    configuration files are out of date.
    --decline       Automatically answer 'n' to all prompts. Records found in
                    the database that don't match configuration files will
                    be left as is and when there's a conflict between certain
                    values (like the contents of the readme) no changes will
                    be made.
    --quiet, -q     Only report errors.
    --verbose, -v   Be chatty.
    --debug, -d     Be extra chatty.
"""
import os
import logging

from docopt import docopt

import datman.config
from datman.exceptions import UndefinedSetting
import dashboard

dashboard.connect_db()

logging.basicConfig(level=logging.WARN,
                    format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(os.path.basename(__file__))


def main():
    args = docopt(__doc__)
    study = args['<study>']
    accept_all = args['--accept']
    skip_all = args['--decline']
    quiet = args['--quiet']
    verbose = args['--verbose']
    debug = args['--debug']

    if verbose:
        logger.setLevel(logging.INFO)
    if debug:
        logger.setLevel(logging.DEBUG)
    if quiet:
        logger.setLevel(logging.ERROR)

    config = datman.config.config()

    if study:
        update_study(study, config)
        return

    update_tags(config, skip_all, accept_all)
    update_studies(config, skip_all, accept_all)


def delete_records(records, prompt=None, delete_func=None, skip_delete=False,
                   delete_all=False):
    logger.debug(f"Found {len(records)} records not defined in config files.")

    if skip_delete:
        logger.debug("Skipping deletion.")
        return

    if not prompt:
        prompt = ("Record {} not specified by config files. If removed any "
                  "records associated with it will also be deleted.")

    if not delete_func:
        def delete_func(x):
            x.delete()

    for record in records:
        if delete_all:
            remove = True
        else:
            remove = prompt_delete(prompt.format(record))

        if not remove:
            logger.info(f"Skipping deletiong of {record}")
            continue

        logger.info(f"Removing {record}")

        try:
            delete_func(record)
        except Exception as e:
            logger.error(f"Failed deleting {record}. Reason - {e}")


def prompt_user(message):
    answer = input(message).strip().lower()
    if answer not in ['y', 'n', '']:
        raise RuntimeError(f"Invalid user input {answer}")
    return answer == 'y'


def prompt_delete(message):
    return prompt_user(message + " Delete? (y/[n]) ")


def update_study(study_id, config, skip_delete=False, delete_all=False):
    try:
        config.set_study(study_id)
    except Exception as e:
        logger.error(f"Can't access config for {study_id}. Reason - {e}")
        return

    try:
        ignore = config.get_key('DbIgnore')
    except UndefinedSetting:
        ignore = False

    if ignore:
        return

    study = dashboard.queries.get_studies(study_id, create=True)

    # Metadata / study-wide settings here
    try:
        descr = config.get_key('Description')
    except UndefinedSetting:
        pass
    else:
        study.description = descr

    try:
        full_name = config.get_key('FullName')
    except UndefinedSetting:
        pass
    else:
        study.name = full_name

    try:
        is_open = config.get_key('IsOpen')
    except UndefinedSetting:
        pass
    else:
        study.is_open = is_open

    update_redcap(config)

    try:
        sites = config.get_sites()
    except UndefinedSetting:
        logger.error(f"No sites defined for {study_id}")
        return

    undefined = [site_id for site_id in study.sites if site_id not in sites]
    delete_records(
        undefined,
        prompt=("Site {} will be deleted from study "
                f"{study.id}. Any records referencing this study/site pair "
                "will be removed."),
        delete_func=lambda x: study.delete_site(x),
        skip_delete=skip_delete,
        delete_all=delete_all
    )

    for site_id in sites:
        update_site(
            study,
            site_id,
            config,
            skip_delete=skip_delete,
            delete_all=delete_all
        )


def update_redcap(config):
    try:
        project = config.get_key("RedcapProjectId")
        instrument = config.get_key("RedcapInstrument")
        url = config.get_key("RedcapUrl")
    except UndefinedSetting:
        return

    rc_config = dashboard.queries.get_redcap_config(
        project, instrument, url, create=True
    )

    if not rc_config:
        logger.error(f"Failed getting config for {project} {instrument} {url}")
        return

    try:
        rc_config.token = read_token(config)
    except Exception:
        pass

    try:
        rc_config.date_field = config.get_key("RedcapDate")
    except UndefinedSetting:
        pass

    try:
        rc_config.comment_field = config.get_key("RedcapComments")
    except UndefinedSetting:
        pass

    try:
        rc_config.session_id_field = config.get_key("RedcapSubj")
    except UndefinedSetting:
        pass

    try:
        rc_config.completed_field = config.get_key("RedcapStatus")
    except UndefinedSetting:
        pass

    try:
        # this could be an issue due to lists...
        rc_config.completed_value = config.get_key("RedcapStatusValue")
    except UndefinedSetting:
        pass

    rc_config.save()


def read_token(config):
    metadata = config.get_path('meta')
    token_file = config.get_key("RedcapToken")
    token_path = os.path.join(metadata, token_file)
    try:
        with open(token_path, "r") as fh:
            return fh.readline().strip()
    except Exception as e:
        logger.error(
            f"Failed to read RedCap token at {token_path}. Reason - {e}"
        )


def update_site(study, site_id, config, skip_delete=False, delete_all=False):
    try:
        code = config.get_key('StudyTag', site=site_id)
    except UndefinedSetting:
        code = None

    try:
        rc_setting = config.get_key('UsesRedcap', site=site_id)
    except UndefinedSetting:
        rc_setting = None

    try:
        notes = config.get_key('UsesTechNotes', site=site_id)
    except UndefinedSetting:
        notes = None

    # try:
    study.update_site(site_id, redcap=rc_setting, notes=notes, code=code,
                      create=True)
    # except Exception as e:
    #     logger.error(f"Failed updating settings for study {study} and site "
    #                  f"{site_id}. Reason - {e}")

    # update_expected_scans(study, site_id, config, skip_delete, delete_all)


# def update_expected_scans(study, site_id, config, skip_delete=False,
#                           delete_all=False):
#     """Update number and type of expected scans for a site.
#     Args:
#         study (:obj:`dashboard.dashboard.models.Study`): A study from the
#             database.
#         site_id (:obj:`str`): The name of a site configured for the study.
#         config (:obj:`datman.config.config`): A config instance for the study.
#         skip_delete (bool, optional): Don't prompt the user and skip deletion
#             of any scan records no longer in the config files.
#         delete_all (bool, optional): Don't prompt the user and delete any
#             scan records no longer in the config files.
#     """
#     try:
#         tag_settings = config.get_tags(site_id)
#     except UndefinedSetting:
#         logger.debug(f"No tags defined for site {site_id}. Skipping update.")
#         return
#
#     if site_id in study.scantypes:
#         undefined = [entry for entry in study.scantypes[site_id]
#                      if entry.scantype_id not in tag_settings]
#         if undefined:
#             delete_records(
#                 undefined,
#                 prompt="Expected scan type {} not defined in config files.",
#                 skip_delete=skip_delete,
#                 delete_all=delete_all
#             )
#
#     for tag in tag_settings:
#         try:
#             sub = tag_settings.get(tag, 'Count')
#         except KeyError:
#             sub = None
#
#         try:
#             pha = tag_settings.get(tag, 'PhaCount')
#         except KeyError:
#             pha = None
#
#         try:
#             study.update_scantype(
#                 site_id, tag, num=sub, pha_num=pha, create=True
#             )
#         except Exception as e:
#             logger.error(f"Failed to update expected scans for {study.id} "
#                          f"site {site_id} and tag {tag}. Reason - {e}.")


def update_tags(config, skip_delete=False, delete_all=False):
    try:
        tag_settings = config.get_key('ExportSettings')
    except UndefinedSetting:
        logger.info('No defined tags found, skipping tag update.')
        return

    for tag in tag_settings:
        db_entry = dashboard.queries.get_scantypes(tag, create=True)[0]

        try:
            qc_type = tag_settings[tag]['QcType']
        except KeyError:
            qc_type = None
        try:
            pha_type = tag_settings[tag]['QcPha']
        except KeyError:
            pha_type = None

        db_entry.qc_type = qc_type
        db_entry.pha_type = pha_type
        db_entry.save()

    all_tags = dashboard.queries.get_scantypes()
    undefined = [record for record in all_tags
                 if record.tag not in tag_settings]

    if not undefined:
        return

    delete_records(
        undefined,
        prompt=("Tag {} undefined. If deleted any scan records with this "
                "tag will also be removed."),
        skip_delete=skip_delete,
        delete_all=delete_all
    )


def update_studies(config, skip_delete=False, delete_all=False):
    try:
        studies = config.get_key('Projects').keys()
    except UndefinedSetting:
        logger.debug('No configured projects detected.')
        return

    all_studies = dashboard.queries.get_studies()

    undefined = [study for study in all_studies
                 if study.id not in studies]

    if undefined:
        delete_records(
            undefined,
            prompt=("Study {} missing from config files. If deleted any "
                    "timepoints and their contents will also be deleted."),
            skip_delete=skip_delete,
            delete_all=delete_all
        )

    for study in studies:
        update_study(study, config, skip_delete, delete_all)


if __name__ == "__main__":
    main()
