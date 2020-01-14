from .forms import UserForm, UserAdminForm


def get_user_form(user, current_user):
    if not current_user.dashboard_admin:
        form = UserForm(obj=user)
        form.account.data = user.username
        return form
    form = get_admin_user_form(user)
    return form


def get_admin_user_form(user):
    form = UserAdminForm(obj=user)
    form.account.data = user.username
    choices = populate_disabled_sites(user)
    form.add_access.choices = choices
    return form


def populate_disabled_sites(user):
    disabled = user.get_disabled_sites()
    choices = []
    for study in disabled:
        if len(disabled[study]) > 1:
            choices.append((study, study + " - ALL"))
        for site in disabled[study]:
            choices.append((study + "-" + site, study + " - " + site))
    return choices


def parse_enabled_sites(new_access):
    """Parses the UserAdminForm add_access field into a dictionary

    Args:
        new_access (:obj:`list`): A list of 'STUDY-SITE' and 'STUDY' strings
        like the sort returned by UserAdminForm.add_access.data

    Returns:
        :obj:`dict`: A dictionary mapping each study to a list of sites to
        enable. The empty list indicates 'all sites'.
    """
    enabled = {}
    for option in new_access:
        fields = option.split('-')
        study = fields[0]
        try:
            site = fields[1]
        except IndexError:
            # Grant user access to all sites for this study
            enabled[study] = []
        else:
            # Grant user access to subset of sites for this study
            if enabled.get(study) == []:
                # If the user is already being given global study access
                # don't accidentally restrict them to a subset of sites
                continue
            enabled.setdefault(study, []).append(site)
    return enabled
