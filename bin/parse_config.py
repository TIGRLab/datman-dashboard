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
                    values no changes will be made.
    --quiet, -q     Only report errors.
    --verbose, -v   Be chatty.
    --debug, -d     Be extra chatty.
"""
import os
import logging

from docopt import docopt

import dashboard
import datman.config
from datman.xnat import get_server
from datman.exceptions import UndefinedSetting

dashboard.connect_db()

logging.basicConfig(level=logging.WARN,
                    format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(os.path.basename(__file__))


def main():
    args = docopt(__doc__)
    study = args["<study>"]
    accept_all = args["--accept"]
    skip_all = args["--decline"]
    quiet = args["--quiet"]
    verbose = args["--verbose"]
    debug = args["--debug"]

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
    """Delete the provided records from the database.

    Args:
        records (:obj:`list`): A list of records from a dashboard database
            table.
        prompt (str, optional): A string to replace the default user prompt.
        delete_func (function, optional): a function that will be called
            to delete each record instead of the default '.delete()' method.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of the records. Useful for debugging.
        delete_all (bool, optional): Don't prompt the user and delete all
            given records.
    """
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
    """Prompt the user and return True if user responds with 'y'.

    Args:
        message (str): The message to show the user.
    """
    answer = input(message).strip().lower()
    if answer not in ["y", "n", ""]:
        raise RuntimeError(f"Invalid user input {answer}")
    return answer == "y"


def prompt_delete(message):
    return prompt_user(message + " Delete? (y/[n]) ")


def update_study(study_id, config, skip_delete=False, delete_all=False):
    """Update all settings stored in the database for the given study.

    Args:
        study_id (str): The ID of the study to update.
        config (:obj:`datman.config.config`): a Datman config object.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of any records no longer defined in the config files.
        delete_all (bool, optional): Don't prompt the user and delete any
            records no longer defined in the config files.
    """
    try:
        config.set_study(study_id)
    except Exception as e:
        logger.error(f"Can't access config for {study_id}. Reason - {e}")
        return

    try:
        ignore = config.get_key("DbIgnore")
    except UndefinedSetting:
        ignore = False

    if ignore:
        return

    study = dashboard.queries.get_studies(study_id, create=True)[0]

    update_setting(study, "description", config, "Description")
    update_setting(study, "name", config, "FullName")
    update_setting(study, "is_open", config, "IsOpen")
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
    """Update the REDCap configuration in the dashboard's database.

    Args:
        config (:obj:`datman.config.config`): A datman config for a study.
    """
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

    update_setting(rc_config, "date_field", config, "RedcapDate")
    update_setting(rc_config, "comment_field", config, "RedcapComments")
    update_setting(rc_config, "session_id_field", config, "RedcapSubj")
    update_setting(rc_config, "completed_field", config, "RedcapStatus")
    update_setting(rc_config, "completed_value", config, "RedcapStatusValue")
    rc_config.save()


def read_token(config):
    """Read the REDCap token from a file defined by the Datman config.

    Args:
        config (:obj:`datman.config.config`): A datman config object for a
            specific study.
    """
    metadata = config.get_path("meta")
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
    """Update the settings in the database for a study's scan site.

    Args:
        study (:obj:`dashboard.models.Study`): A study from the database.
        site_id (:obj:`str`): The name of a site that should be associated
            with this study or a site from the study that should have its
            settings updated.
        config (:obj:`datman.config.config`): A datman config instance
            for the study.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of any site records no longer in the config files.
        delete_all (bool, optional): Don't prompt the user and delete any
            site records no longer in the config files.
    """
    settings = collect_settings(
        config,
        {
            "code": "StudyTag",
            "redcap": "UsesRedcap",
            "notes": "UsesTechNotes",
            "xnat_archive": "XnatArchive",
            "xnat_convention": "XnatConvention"
        },
        site=site_id
    )

    try:
        xnat_fname = config.get_key("XnatCredentials", site=site_id)
        settings["xnat_credentials"] = os.path.join(
            config.get_path("meta"), xnat_fname
        )
    except UndefinedSetting:
        pass

    try:
        settings["xnat_url"] = get_server(config)
    except UndefinedSetting:
        pass

    settings["create"] = True

    try:
        study.update_site(site_id, **settings)
    except Exception as e:
        logger.error(f"Failed updating settings for study {study} and site "
                     f"{site_id}. Reason - {e}")

    update_expected_scans(study, site_id, config, skip_delete, delete_all)


def update_expected_scans(study, site_id, config, skip_delete=False,
                          delete_all=False):
    """Update number and type of expected scans for a site.

    Args:
        study (:obj:`dashboard.dashboard.models.Study`): A study from the
            database.
        site_id (:obj:`str`): The name of a site configured for the study.
        config (:obj:`datman.config.config`): A config instance for the study.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of any records no longer defined in the config files.
        delete_all (bool, optional): Don't prompt the user and delete any
            records no longer defined in the config files.
    """
    try:
        tag_settings = config.get_tags(site_id)
    except UndefinedSetting:
        logger.debug(f"No tags defined for site {site_id}. Skipping update.")
        return

    if site_id in study.scantypes:
        undefined = [entry for entry in study.scantypes[site_id]
                     if entry.scantype_id not in tag_settings]
        if undefined:
            delete_records(
                undefined,
                prompt="Expected scan type {} not defined in config files.",
                skip_delete=skip_delete,
                delete_all=delete_all
            )

    for tag in tag_settings:
        try:
            sub = tag_settings.get(tag, "Count")
        except KeyError:
            sub = None

        try:
            pha = tag_settings.get(tag, "PhaCount")
        except KeyError:
            pha = None

        try:
            study.update_scantype(
                site_id, tag, num=sub, pha_num=pha, create=True
            )
        except Exception as e:
            logger.error(f"Failed to update expected scans for {study.id} "
                         f"site {site_id} and tag {tag}. Reason - {e}.")


def update_tags(config, skip_delete=False, delete_all=False):
    """Update the tags defined in the database.

    Args:
        config (:obj:`datman.datman.config`): A datman config object.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of any scantype records no longer defined in the config files.
        delete_all (bool, optional): Don't prompt the user and delete any
            scantype records no longer defined in the config files.
    """
    try:
        tag_settings = config.get_key("ExportSettings")
    except UndefinedSetting:
        logger.info("No defined tags found, skipping tag update.")
        return

    for tag in tag_settings:
        db_entry = dashboard.queries.get_scantypes(tag, create=True)[0]

        try:
            qc_type = tag_settings[tag]["QcType"]
        except KeyError:
            qc_type = None
        try:
            pha_type = tag_settings[tag]["QcPha"]
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
    """Update the settings in the database for all studies.

    Args:
        config (:obj:`datman.config.config`): a datman config object.
        skip_delete (bool, optional): Don't prompt the user and skip deletion
            of any study records no longer defined in the config files.
        delete_all (bool, optional): Don't prompt the user and delete any
            study records no longer defined in the config files.
    """
    try:
        studies = config.get_key("Projects").keys()
    except UndefinedSetting:
        logger.debug("No configured projects detected.")
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


def update_setting(record, attribute, config, key, site=None):
    try:
        value = config.get_key(key, site=site)
    except UndefinedSetting:
        pass
    else:
        setattr(record, attribute, value)


def collect_settings(config, key_map, site=None):
    all_vals = {}
    for attr_name in key_map:
        try:
            val = config.get_key(key_map[attr_name], site=site)
        except UndefinedSetting:
            val = None
        all_vals[attr_name] = val
    return all_vals


if __name__ == "__main__":
    main()
