"""Configuration to modify menu contents.
"""
import logging
import os

from pydantic import BaseModel, ValidationError
import yaml

logger = logging.getLogger(__name__)


class MenuItem(BaseModel):
    """Create a MenuItem object for each button to add to dashboard menus.
    """
    menu: str
    btn_text: str
    url: str
    hover_text: str = None
    name: str = None


def get_menu_config():
    """Gets the menu config file and parses it for the dashboard to use.
    """
    menu_file = os.environ.get("DASH_MENU_CONFIG")

    if not menu_file:
        return {}

    try:
        with open(menu_file) as fh:
            contents = yaml.load(fh, Loader=yaml.SafeLoader)
    except (FileNotFoundError, PermissionError, yaml.parser.ParserError) as e:
        logger.error(f"Could not read 'DASH_MENU_CONFIG' file {menu_file}. "
                     f"Custom menu items can not be added. Reason - {e}")
        return {}

    menu_config = {}
    for btn in contents:
        try:
            item = MenuItem(name=btn, **contents[btn])
        except ValidationError as e:
            logger.error(
                f"Skipping entry '{btn}' in DASH_MENU_CONFIG' file {menu_file}"
                f" Reason - {e}"
            )
            continue
        menu_config.setdefault(item.menu, []).append(item)

    return menu_config


MENU_ITEMS = get_menu_config()
