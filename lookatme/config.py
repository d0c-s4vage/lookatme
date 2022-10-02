"""
Config module for lookatme
"""


import os

LOG = None
STYLE = None

# default to the current working directory - this will be set later by
# pres:Presentation when reading the input stream
SLIDE_SOURCE_DIR = os.getcwd()
