"""
Defines a calendar extension that overrides code block rendering if the
language type is calendar
"""


import datetime
import calendar
import urwid


from lookatme.exceptions import IgnoredByContrib


def user_warnings():
    """No warnings exist for this extension. Anything you want to warn the
    user about, such as security risks in processing untrusted markdown, should
    go here.
    """
    return []


def render_code(token, body, stack, loop):
    lang = token["lang"] or ""
    if lang != "calendar":
        raise IgnoredByContrib()
    
    today = datetime.datetime.utcnow()
    return urwid.Text(calendar.month(today.year, today.month))
