"""
Config module for lookatme
"""


import logging
import os
from types import ModuleType
from typing import Any, Dict

import lookatme.themes
from lookatme.utils import dict_deep_update

LOG = None
STYLE: Dict[str, Any] = {}


def get_log() -> logging.Logger:
    global LOG
    if LOG is None:
        import lookatme.log

        LOG = lookatme.log.create_log()
    return LOG


def get_style() -> Dict:
    if not STYLE:
        raise Exception("STYLE was empty!")
    return STYLE


def get_style_with_precedence(
    theme_mod: ModuleType,
    direct_overrides: Dict,
) -> Dict[str, Any]:
    """Return the resulting style dict from the provided override values."""
    # style override order:
    # 1. theme settings
    styles = lookatme.themes.ensure_defaults(theme_mod)
    # 2. inline styles from the presentation
    dict_deep_update(styles, direct_overrides)
    # 3. CLI style overrides
    # TODO

    return styles


def set_global_style_with_precedence(
    theme_mod,
    direct_overrides,
) -> Dict[str, Any]:
    """Set the lookatme.config.STYLE value based on the provided override
    values
    """
    global STYLE
    STYLE = get_style_with_precedence(theme_mod, direct_overrides)

    return STYLE


# default to the current working directory - this will be set later by
# pres:Presentation when reading the input stream
SLIDE_SOURCE_DIR = os.getcwd()
