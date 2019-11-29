"""
Logging module
"""


import logging


def create_log(log_path):
    """Create a new log that writes to log_path
    """
    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    return logging.getLogger("lookatme")


def create_null_log():
    """Create a logging object that does nothing
    """
    logging.basicConfig(handlers=[logging.NullHandler()])
    return logging.getLogger("lookatme")
