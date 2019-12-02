"""
Defines render functions that render lexed markdown block tokens into urwid
representations
"""


import pygments
import pygments.formatters
import pygments.lexers
import pygments.styles
import mistune
import re
import shlex
import urwid


import lookatme.config as config
from lookatme.contrib import contrib_first
import lookatme.render.pygments as pygments_render
import lookatme.render.markdown_inline as markdown_inline_renderer
from lookatme.utils import *


def _meta(item):
    if not hasattr(item, "meta"):
        meta = {}
        setattr(item, "meta", meta)
    else:
        meta = getattr(item, "meta")
    return meta


def _set_is_list(item, level=1):
    _meta(item).update({
        "is_list": True,
        "list_level": level,
    })


def _is_list(item):
    return _meta(item).get("is_list", False)


def _list_level(item):
    return _meta(item).get("list_level", 1)


@contrib_first
def render_heading(token, body, stack, loop):
    headings = config.STYLE["headings"]
    level = token["level"]
    style = config.STYLE["headings"].get(str(level), headings["default"])

    prefix = styled_text(style["prefix"], style)
    suffix = styled_text(style["suffix"], style)

    rendered = render_text(text=token["text"])
    styled_rendered = styled_text(rendered, style, supplement_style=True)

    return [
        urwid.Divider(),
        urwid.Text([prefix] + styled_text(rendered, style) + [suffix]),
        urwid.Divider(),
    ]


@contrib_first
def render_table(token, body, stack, loop):
    """Render a table token
    """
    from lookatme.widgets.table import Table

    headers = token["header"]
    aligns = token["align"]
    cells = token["cells"]

    table = Table(cells, headers=headers, aligns=aligns)
    return urwid.Padding(table, width=table.total_width + 2, align="center")


@contrib_first
def render_list_start(token, body, stack, loop):
    res = urwid.Pile(urwid.SimpleFocusListWalker([]))

    in_list = _is_list(stack[-1])
    list_level = 1
    if in_list:
        list_level = _list_level(stack[-1]) + 1
    _set_is_list(res, list_level)
    stack.append(res)

    widgets = []
    if not in_list:
        widgets.append(urwid.Divider())
    widgets.append(urwid.Padding(res, left=2))
    if not in_list:
        widgets.append(urwid.Divider())
    return widgets


@contrib_first
def render_list_end(token, body, stack, loop):
    stack.pop()


def _list_item_start(token, body, stack, loop):
    list_level = _list_level(stack[-1])
    pile = urwid.Pile(urwid.SimpleFocusListWalker([]))

    bullets = config.STYLE["bullets"]
    list_bullet = bullets.get(str(list_level), bullets["default"])

    res = urwid.Columns([
        (2, urwid.Text(("bold", list_bullet + " "))),
        pile,
    ])
    stack.append(pile)
    return res


@contrib_first
def render_list_item_start(token, body, stack, loop):
    return _list_item_start(token, body, stack, loop)


@contrib_first
def render_loose_item_start(token, body, stack, loop):
    return _list_item_start(token, body, stack, loop)


@contrib_first
def render_list_item_end(token, body, stack, loop):
    stack.pop()


@contrib_first
def render_text(token=None, body=None, stack=None, loop=None, text=None):
    if text is None:
        text = token["text"]

    inline_lexer = mistune.InlineLexer(markdown_inline_renderer)
    res = inline_lexer.output(text)
    return urwid.Text(res)
render_paragraph = render_text


@contrib_first
def render_block_quote_start(token, body, stack, loop):
    pile = urwid.Pile([])
    stack.append(pile)

    styles = config.STYLE["quote"]

    quote_side = styles["side"]
    quote_top_corner = styles["top_corner"]
    quote_bottom_corner = styles["bottom_corner"]
    quote_style = styles["style"]

    return [
        urwid.Divider(),
        urwid.LineBox(
            urwid.AttrMap(
                urwid.Padding(pile, left=2),
                spec_from_style(quote_style),
            ),
            lline=quote_side, rline="",
            tline=" ", trcorner="", tlcorner=quote_top_corner,
            bline=" ", brcorner="", blcorner=quote_bottom_corner,
        ),
        urwid.Divider(),
    ]


@contrib_first
def render_block_quote_end(token, body, stack, loop):
    stack.pop()


@contrib_first
def render_code(token, body, stack, loop):
    lang = token.get("lang", "text") or "text"
    res = pygments_render.render_text(token["text"], lang=lang)

    return [
        urwid.Divider(),
        res,
        urwid.Divider(),
    ]
