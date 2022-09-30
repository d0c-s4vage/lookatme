"""
Config module for lookatme
"""


import os
import logging
from typing import Optional, Dict


LOG: logging.Logger = logging.getLogger(__name__)
STYLE: Dict = {}


# default to the current working directory - this will be set later by
# pres:Presentation when reading the input stream
SLIDE_SOURCE_DIR = os.getcwd()
