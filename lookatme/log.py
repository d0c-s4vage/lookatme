"""
Logging module
"""


import logging


def create_log(log_path):
    """Create a new log that writes to log_path"""
    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    res = logging.getLogger("lookatme")

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.ERROR)
    res.addHandler(stderr_handler)

    logging.getLogger("markdown_it").setLevel(logging.CRITICAL)

    return res


def create_null_log():
    """Create a logging object that does nothing"""
    logging.basicConfig(handlers=[logging.NullHandler()])
    return logging.getLogger("lookatme")
