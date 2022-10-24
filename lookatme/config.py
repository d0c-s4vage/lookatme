"""
Config module for lookatme
"""


import logging
import os
from typing import Any, Dict

import lookatme.themes
from lookatme.utils import dict_deep_update

LOG = None
STYLE: Dict[str, Any] = {}


def get_log() -> logging.Logger:
    if LOG is None:
        raise Exception("LOG was None")
    return LOG


def get_style() -> Dict:
    if not STYLE:
        raise Exception("STYLE was empty!")
    return STYLE


def get_style_with_precedence(theme_mod, direct_overrides, style_override):
    # style override order:
    # 1. theme settings
    styles = lookatme.themes.ensure_defaults(theme_mod)
    # 2. inline styles from the presentation
    dict_deep_update(styles, direct_overrides)
    # 3. CLI style overrides
    if style_override is not None:
        styles["style"] = style_override  # type: ignore

    return styles


def set_global_style_with_precedence(theme_mod, direct_overrides, style_override) -> Dict[str, Any]:
    global STYLE
    STYLE = get_style_with_precedence(
        theme_mod, direct_overrides, style_override)

    return STYLE


# default to the current working directory - this will be set later by
# pres:Presentation when reading the input stream
SLIDE_SOURCE_DIR = os.getcwd()
