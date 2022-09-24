"""
Defines render functions that render lexed markdown block tokens into urwid
representations
"""


import copy
import pygments
import pygments.formatters
import pygments.lexers
import pygments.styles
import mistune
import re
import shlex
import sys
import urwid


import lookatme.config as config
from lookatme.contrib import contrib_first
import lookatme.render.pygments as pygments_render
import lookatme.render.markdown_inline as markdown_inline
from lookatme.utils import *
from lookatme.widgets.clickable_text import ClickableText
from lookatme.render.context import Context
from lookatme.render.markdown_html import LookatmeHTMLParser


THIS_MOD = sys.modules[__name__]


def _set_is_list(item, level=1, ordered=False):
    get_meta(item).update({
        "is_list": True,
        "list_level": level,
        "ordered": ordered,
        "item_count": 0,
    })


def _inc_item_count(item):
    get_meta(item)["item_count"] += 1
    return get_meta(item)["item_count"]


def _is_list(item):
    return get_meta(item).get("is_list", False)


def _list_level(item):
    return get_meta(item).get("list_level", 1)


# =============================================================================


def render(token, ctx: Context):
    """Render a single token
    """
    with ctx.level_inc():
        render_token = getattr(THIS_MOD, "render_{}".format(token["type"]))
        res = render_token(token, ctx)

        if res is not None:
            pile_or_listbox_add(ctx.container, res)

        return res


def render_all(tokens, ctx: Context):
    for token in tokens:
        ctx.log_debug("Rendering block token: {!r}".format(token))
        render(token, ctx)


def render_tokens_full(tokens, loop):
    ctx = Context(loop)
    ctx.container_push(urwid.ListBox([]))
    for token in tokens:
        render(token, ctx)
    return ctx.container.body


@contrib_first
def render_newline(token, ctx: Context):
    """Render a newline

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    return urwid.Divider()


@contrib_first
def render_hrule(token, ctx: Context):
    """Render a newline

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    hrule_conf = config.STYLE["hrule"]
    div = urwid.Divider(hrule_conf['char'], top=1, bottom=1)
    return urwid.Pile([urwid.AttrMap(div, spec_from_style(hrule_conf['style']))])


@contrib_first
def render_heading(token, ctx: Context):
    """Render markdown headings, using the defined styles for the styling and
    prefix/suffix.

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.

    Below are the default stylings for headings:

    .. code-block:: yaml

        headings:
          '1':
            bg: default
            fg: '#9fc,bold'
            prefix: "██ "
            suffix: ""
          '2':
            bg: default
            fg: '#1cc,bold'
            prefix: "▓▓▓ "
            suffix: ""
          '3':
            bg: default
            fg: '#29c,bold'
            prefix: "▒▒▒▒ "
            suffix: ""
          '4':
            bg: default
            fg: '#66a,bold'
            prefix: "░░░░░ "
            suffix: ""
          default:
            bg: default
            fg: '#579,bold'
            prefix: "░░░░░ "
            suffix: ""

    :returns: A list of urwid Widgets or a single urwid Widget
    """
    headings = config.STYLE["headings"]
    level = token["level"]
    style = config.STYLE["headings"].get(str(level), headings["default"])

    prefix = styled_text(style["prefix"], style)
    suffix = styled_text(style["suffix"], style)

    header_spec = spec_from_style(style)
    with ctx.use_spec(header_spec):
        markdown_inline.render_all(token["children"], ctx)

    return [urwid.Divider()] + ctx.inline_widgets_consumed + [urwid.Divider()]


@contrib_first
def render_table(token, ctx: Context):
    """Renders a table using the :any:`Table` widget.

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.

    The table widget makes use of the styles below:

    .. code-block:: yaml

        table:
          column_spacing: 3
          header_divider: "─"

    :returns: A list of urwid Widgets or a single urwid Widget
    """
    from lookatme.widgets.table import Table

    table_header = None
    table_body = None

    for child_token in token["children"]:
        if child_token["type"] == "table_head":
            table_header = child_token
        elif child_token["type"] == "table_body":
            table_body = child_token
        else:
            raise NotImplementedError("Unsupported table child token: {!r}".format(child_token["type"]))

    table = Table(header=table_header, body=table_body, ctx=ctx)
    padding = urwid.Padding(table, width=table.total_width + 2, align="center")

    def table_changed(*args, **kwargs):
        padding.width = table.total_width + 2

    urwid.connect_signal(table, "change", table_changed)

    return padding


@contrib_first
def render_list(token, ctx: Context):
    """Handles the indentation when starting rendering a new list. List items
    themselves (with the bullets) are rendered by the
    :any:`render_list_item_start` function.

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    res = urwid.Pile([])

    in_list = _is_list(ctx.container)
    _set_is_list(res, token["level"], ordered=token['ordered'])

    get_meta(res)['list_start_token'] = token
    get_meta(res)['max_list_marker_width'] = token.get('max_list_marker_width', 2)

    with ctx.use_container(res):
        for child_token in token["children"]:
            render(child_token, ctx)

    meta = get_meta(res)
    meta['list_start_token']['max_list_marker_width'] = meta['max_list_marker_width']

    wrapped_res = urwid.AttrMap(res, {None: ctx.spec_general})

    widgets = []
    if not in_list:
        widgets.append(urwid.Divider())
        widgets.append(urwid.Padding(wrapped_res, left=2))
        widgets.append(urwid.Divider())
        return widgets
    return res


@contrib_first
def render_list_item(token, ctx: Context):
    """Render the start of a list item. This function makes use of two
    different styles, one each for unordered lists (bullet styles) and ordered
    lists (numbering styles):

    .. code-block:: yaml

        bullets:
          '1': "•"
          '2': "⁃"
          '3': "◦"
          default: "•"
        numbering:
          '1': "numeric"
          '2': "alpha"
          '3': "roman"
          default: "numeric"

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    list_level = token["level"]
    curr_count = _inc_item_count(ctx.container)
    pile = urwid.Pile(urwid.SimpleFocusListWalker([]))

    meta = get_meta(ctx.container)

    if meta["ordered"]:
        numbering = config.STYLE["numbering"]
        list_marker_type = numbering.get(str(list_level), numbering["default"])
        sequence = {
            "numeric": lambda x: str(x),
            "alpha": lambda x: chr(ord("a") + x - 1),
            "roman": lambda x: int_to_roman(x),
        }[list_marker_type]
        list_marker = sequence(curr_count) + "."
    else:
        bullets = config.STYLE["bullets"]
        list_marker = bullets.get(str(list_level), bullets["default"])

    marker_text = list_marker + " "
    if len(marker_text) > meta["max_list_marker_width"]:
        meta["max_list_marker_width"] = len(marker_text)
    marker_col_width = meta['max_list_marker_width']

    res = urwid.Columns([
        (marker_col_width, urwid.Text(("bold", marker_text))),
        pile,
    ])

    with ctx.use_container(pile):
        for child_token in token["children"]:
            render(child_token, ctx)

    pile_or_listbox_add(pile, ctx.inline_widgets_consumed)

    return res


@contrib_first
def render_block_text(token, ctx: Context):
    """Render block text
    """
    markdown_inline.render_all(token["children"], ctx)
    # let the inline render results continue!
    # return ctx.inline_widgets_consumed
    return []


@contrib_first
def render_block_html(token, ctx: Context):
    """Render block html
    """
    LookatmeHTMLParser(ctx).feed(token["text"])
    return ctx.inline_widgets_consumed


@contrib_first
def render_paragraph(token, ctx: Context):
    """Renders the provided text with additional pre and post paddings.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    markdown_inline.render_all(token["children"], ctx)
    # return [urwid.Divider()] + ctx.inline_widgets_consumed + [urwid.Divider()]
    return ctx.inline_widgets_consumed


@contrib_first
def render_block_quote(token, ctx: Context):
    """

    This function makes use of the styles:

    .. code-block:: yaml

        quote:
          top_corner: "┌"
          bottom_corner: "└"
          side: "╎"
          style:
            bg: default
            fg: italics,#aaa

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    pile = urwid.Pile([])

    styles = config.STYLE["quote"]

    quote_side = styles["side"]
    quote_top_corner = styles["top_corner"]
    quote_bottom_corner = styles["bottom_corner"]
    quote_style = styles["style"]

    with ctx.use_container(pile):
        with ctx.use_spec(spec_from_style(quote_style)):
            for child_token in token["children"]:
                render(child_token, ctx)

    # remove leading/trailing divider if they were added to the pile
    if isinstance(pile.contents[0][0], urwid.Divider):
        pile.contents = pile.contents[1:]
    if isinstance(pile.contents[-1][0], urwid.Divider):
        pile.contents = pile.contents[:-1]

    return [
        urwid.LineBox(
            urwid.AttrMap(
                urwid.Padding(pile, left=2),
                spec_from_style(quote_style),
            ),
            lline=quote_side, rline="",
            tline=" ", trcorner="", tlcorner=quote_top_corner,
            bline=" ", brcorner="", blcorner=quote_bottom_corner,
        ),
    ]


@contrib_first
def render_block_code(token, ctx: Context):
    """Renders a code block using the Pygments library.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    info = token.get("info", None) or "text"
    lang = info.split()[0]
    # TODO support line highlighting, etc?
    text = token["text"]
    res = pygments_render.render_text(text, lang=lang)

    return [
        urwid.Divider(),
        res,
        urwid.Divider()
    ]
