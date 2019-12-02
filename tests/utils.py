"""
Defines utilities for testing lookatme
"""


import pytest


def spec_and_text(item):
    """``item`` should be an item from a rendered widget, a tuple of the form

    .. code-block:: python

        (spec, ?, text)
    """
    return item[0], item[2]


def row_text(rendered_row):
    """Return all text joined together from the rendered row
    """
    return b"".join(x[-1] for x in rendered_row)
