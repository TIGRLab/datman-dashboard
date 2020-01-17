import os
import json

from ...datman_utils import get_study_path


def get_nifti_path(scan):
    study = scan.get_study().id
    nii_folder = get_study_path(study, folder='nii')
    fname = "_".join([scan.name, scan.description + ".nii.gz"])

    full_path = os.path.join(nii_folder, scan.timepoint, fname)
    if not os.path.exists(full_path):
        full_path = full_path.replace(".nii.gz", ".nii")

    return full_path


def update_json(scan, contents):
    scan.json_contents = contents
    scan.save()

    updated_jsons = get_study_path(scan.get_study().id, "jsons")
    json_folder = os.path.join(updated_jsons, scan.timepoint)
    try:
        os.makedirs(json_folder)
    except FileExistsError:
        pass
    new_json = os.path.join(json_folder, os.path.basename(scan.json_path))

    with open(new_json, "w") as out:
        json.dump(contents, out)

    os.remove(scan.json_path)
    os.symlink(
        os.path.join(
            os.path.relpath(json_folder, os.path.dirname(scan.json_path)),
            os.path.basename(scan.json_path)), scan.json_path)
