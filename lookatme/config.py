"""
Config module for lookatme
"""


import logging
import os
from typing import Dict, Optional

LOG = None
STYLE: Optional[Dict] = None


def get_log() -> logging.Logger:
    if LOG is None:
        raise Exception("LOG was None")
    return LOG


def get_style() -> Dict:
    if STYLE is None:
        raise Exception("STYLE was None!")
    return STYLE


# default to the current working directory - this will be set later by
# pres:Presentation when reading the input stream
SLIDE_SOURCE_DIR = os.getcwd()
