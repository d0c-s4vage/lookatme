"""
This module defines a built-in contrib module that enables terminal embedding
within a slide.
"""


import os
import shlex
import signal
import urwid


from lookatme.exceptions import IgnoredByContrib


CREATED_TERMS = []


def render_code(token, body, stack, loop):
    lang = token["lang"] or ""
    if not lang.startswith("terminal"):
        raise IgnoredByContrib

    rows = lang.replace("terminal", "").strip()
    if len(rows) != 0:
        rows = int(rows)

    term = urwid.Terminal(
        shlex.split(token["text"].strip()),
        main_loop=loop,
        encoding="utf8",
    )
    CREATED_TERMS.append(term)

    res = urwid.LineBox(urwid.BoxAdapter(term, height=rows))

    return [
        urwid.Divider(),
        res,
        urwid.Divider(),
    ]


def shutdown():
    for term in CREATED_TERMS:
        if term.pid is not None:
            term.terminate()
