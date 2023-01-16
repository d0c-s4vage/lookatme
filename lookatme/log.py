"""
Logging module
"""


import logging
import os
import tempfile
from typing import Optional


def create_log(log_path: Optional[str] = None):
    """Create a new log that writes to log_path"""

    log_path = log_path or os.path.join(tempfile.gettempdir(), "lookatme.log")

    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    res = logging.getLogger("lookatme")

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.INFO)
    res.addHandler(stderr_handler)

    logging.getLogger("markdown_it").setLevel(logging.CRITICAL)

    return res


def create_null_log():
    """Create a logging object that does nothing"""
    logging.basicConfig(handlers=[logging.NullHandler()])
    return logging.getLogger("lookatme")
