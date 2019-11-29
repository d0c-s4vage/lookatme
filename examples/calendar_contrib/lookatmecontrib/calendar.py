"""
Defines a calendar extension that overrides code block rendering if the
language type is calendar
"""


import datetime
import calendar
import urwid


from lookatme.exceptions import IgnoredByContrib


def render_code(token, body, stack, loop):
    lang = token["lang"] or ""
    if lang != "calendar":
        raise IgnoredByContrib()
    
    today = datetime.datetime.utcnow()
    return urwid.Text(calendar.month(today.year, today.month))
