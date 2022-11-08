"""
Defines render functions that render lexed markdown block tokens into urwid
representations
"""


import copy
import pygments
import pygments.styles
import re
import sys
from typing import Dict, List, Tuple, Union

import urwid

import lookatme.config as config
import lookatme.render.markdown_inline as markdown_inline
import lookatme.render.pygments as pygments_render
from lookatme.contrib import contrib_first
from lookatme.render.context import Context
from lookatme.tutorial import tutor
from lookatme.widgets.fancy_box import FancyBox
import lookatme.utils as utils

THIS_MOD = sys.modules[__name__]


def _ctx_style_spec(style: Dict, ctx: Context) -> Union[None, urwid.AttrSpec]:
    return ctx.spec_text_with(utils.spec_from_style(style))


# =============================================================================


def render(token, ctx: Context):
    """Render a single token"""
    with ctx.level_inc():
        token_type = token["type"].lower()
        render_fn = getattr(THIS_MOD, "render_{}".format(token_type), None)
        if render_fn is None:
            raise NotImplementedError(
                "Rendering {!r} tokens is not implemented".format(token_type)
            )

        render_fn(token, ctx)


def render_all(ctx: Context):
    for token in ctx.tokens:
        ctx.log_debug("Rendering block token: {!r}".format(token))
        render(token, ctx)


@tutor(
    "markdown",
    "paragraph",
    r"""
    Paragraphs in markdown are simply text with a full empty line between them:

    <TUTOR:EXAMPLE>
    paragraph 1

    paragraph 2
    </TUTOR:EXAMPLE>

    ## Style

    Paragraphs cannot be styled in lookatme.
    """,
)
@contrib_first
def render_paragraph_open(token, ctx: Context):
    """ """
    next_token = ctx.tokens.peek()

    # don't ensure a new block for paragraphs that contain a single
    # html_inline token!
    if (
        next_token is not None
        and next_token["type"] == "inline"
        and len(next_token["children"]) == 1
        and next_token["children"][0]["type"] == "html_inline"
    ):
        return

    ctx.ensure_new_block()


@contrib_first
def render_paragraph_close(token, ctx: Context):
    """ """
    pass


@contrib_first
def render_inline(token, ctx: Context):
    """ """
    with ctx.use_tokens(token.get("children", [])):
        markdown_inline.render_all(ctx)


@contrib_first
def render_ordered_list_open(token, ctx: Context):
    """ """
    render_list_open(token, ctx, ordered=True)


@contrib_first
def render_bullet_list_open(token, ctx: Context):
    """ """
    render_list_open(token, ctx, ordered=False)


@contrib_first
def render_list_open(token, ctx: Context, ordered: bool):
    list_container = urwid.Pile([])

    level = 1
    prev_meta = ctx.meta
    in_list = prev_meta.get("is_list", False)
    if in_list:
        level = prev_meta["level"] + 1
    else:
        ctx.ensure_new_block()

    ctx.container_push(list_container, is_new_block=True)

    new_meta = ctx.meta
    new_meta["is_list"] = True
    new_meta["level"] = level
    new_meta["ordered"] = ordered
    new_meta["item_count"] = 0
    new_meta["list_start_token"] = token
    new_meta["max_list_marker_width"] = token.get("max_list_marker_width", 2)


@contrib_first
def render_ordered_list_close(token, ctx: Context):
    """ """
    render_list_close(token, ctx)


@contrib_first
def render_bullet_list_close(token, ctx: Context):
    """ """
    render_list_close(token, ctx)


@contrib_first
def render_list_close(_, ctx: Context):
    """ """
    meta = ctx.meta
    meta["list_start_token"]["max_list_marker_width"] = meta["max_list_marker_width"]

    ctx.container_pop()


@tutor(
    "markdown",
    "ordered lists",
    r"""
    Ordered lists are lines of text prefixed by a `N. ` or `N)`, where `N` is
    any number.

    <TUTOR:EXAMPLE>
    1. item
    1. item
        1. item
            5. item
            6. item
        1. item
    1. item
    </TUTOR:EXAMPLE>

    ## Style

    Ordered lists can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>numbering</TUTOR:STYLE>
    """,
)
@tutor(
    "markdown",
    "unordered lists",
    r"""
    Unordered lists are lines of text starting with either `*`, `+`, or `-`.

    <TUTOR:EXAMPLE>
    * item
    * item
        * item
            * item
            * item
        * item
    * item
    </TUTOR:EXAMPLE>

    ## Style

    Unordered lists can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>bullets</TUTOR:STYLE>
    """,
)
@tutor(
    "markdown",
    "lists",
    r"""
    Lists can either be ordered or unordered. You can nest lists by indenting
    child lists by four spaces.

    Other markdown elements can also be nested in lists.

    <TUTOR:EXAMPLE>
    1. item
       > quote
    1. item
        * item
            1. item
               a paragraph

               More text here blah blah blah
            1. A new item
        * item
           ```python
           print("hello")
           ```
    1. item
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_list_item_open(_, ctx: Context):
    """ """
    meta = ctx.meta
    list_level = meta["level"]

    meta["item_count"] += 1
    curr_count = meta["item_count"]

    pile = urwid.Pile(urwid.SimpleFocusListWalker([]))

    if meta["ordered"]:
        numbering = config.get_style()["numbering"]
        marker_style = numbering.get(str(list_level), numbering["default"])
        marker_type = marker_style["text"]
        sequence = {
            "numeric": lambda x: str(x),
            "alpha": lambda x: chr(ord("a") + x - 1),
            "roman": lambda x: utils.int_to_roman(x),
        }[marker_type]
        marker_text = sequence(curr_count) + "."
    else:
        bullets = config.get_style()["bullets"]
        marker_style = bullets.get(str(list_level), bullets["default"])
        marker_text = marker_style["text"]

    marker_spec = utils.spec_from_style(marker_style)
    if len(marker_text) + 1 > meta["max_list_marker_width"]:
        meta["max_list_marker_width"] = len(marker_text) + 1
    marker_col_width = meta["max_list_marker_width"]

    res = urwid.Columns(
        [
            (
                marker_col_width,
                urwid.Text(
                    (ctx.spec_text_with(marker_spec), marker_text),
                ),
            ),
            pile,
        ]
    )

    ctx.container_push(pile, is_new_block=True, custom_add=res)


@contrib_first
def render_list_item_close(_, ctx: Context):
    """ """
    ctx.container_pop()


@tutor(
    "markdown",
    "headings",
    r"""
    Headings are specified by prefixing text with `#` characters:

    <TUTOR:EXAMPLE>
    ## Heading Level 2
    ### Heading Level 3
    #### Heading Level 4
    ##### Heading Level 5
    </TUTOR:EXAMPLE>

    ## Style

    Headings can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>headings</TUTOR:STYLE>
    """,
)
@contrib_first
@contrib_first
def render_heading_open(token: Dict, ctx: Context):
    """ """
    headings = config.get_style()["headings"]
    level = token["level"]
    style = config.get_style()["headings"].get(str(level), headings["default"])

    ctx.ensure_new_block()

    header_spec = utils.spec_from_style(style)
    ctx.spec_push(header_spec)
    prefix_token = {"type": "text", "content": style["prefix"]}
    markdown_inline.render(prefix_token, ctx)


@contrib_first
def render_heading_close(token: Dict, ctx: Context):
    """ """
    headings = config.get_style()["headings"]
    level = int(token["tag"].replace("h", ""))
    style = config.get_style()["headings"].get(str(level), headings["default"])

    suffix_token = {"type": "text", "content": style["suffix"]}
    markdown_inline.render(suffix_token, ctx)

    ctx.spec_pop()
    ctx.ensure_new_block()


@tutor(
    "markdown",
    "block quote",
    r"""
    Block quotes are lines of markdown prefixed with `> `. Block quotes can
    contain text, other markdown, and can even be nested!

    <TUTOR:EXAMPLE>
    > Some quoted text
    > > > > # Heading
    > > > >
    > > > *hello world*
    > > >
    > > ~~apples~~
    > >
    > space chips
    </TUTOR:EXAMPLE>



    ## Style

    Block quotes can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>quote</TUTOR:STYLE>
    """,
)
@contrib_first
def render_blockquote_open(token: Dict, ctx: Context):
    """ """
    ctx.ensure_new_block()

    pile = urwid.Pile([])

    quote_style = config.get_style()["quote"]
    border_style = quote_style["border"]

    inner_spec = ctx.spec_text_with(utils.spec_from_style(quote_style["style"]))

    box = FancyBox(
        ctx.wrap_widget(urwid.Padding(pile, left=2), spec=inner_spec),
        tl_corner=border_style["tl_corner"]["text"],
        tr_corner=border_style["tr_corner"]["text"],
        br_corner=border_style["br_corner"]["text"],
        bl_corner=border_style["bl_corner"]["text"],
        tl_corner_spec=_ctx_style_spec(border_style["tl_corner"], ctx),
        tr_corner_spec=_ctx_style_spec(border_style["tr_corner"], ctx),
        br_corner_spec=_ctx_style_spec(border_style["br_corner"], ctx),
        bl_corner_spec=_ctx_style_spec(border_style["bl_corner"], ctx),
        t_fill=border_style["t_line"]["text"],
        r_fill=border_style["r_line"]["text"],
        b_fill=border_style["b_line"]["text"],
        l_fill=border_style["l_line"]["text"],
        t_fill_spec=_ctx_style_spec(border_style["t_line"], ctx),
        r_fill_spec=_ctx_style_spec(border_style["r_line"], ctx),
        b_fill_spec=_ctx_style_spec(border_style["b_line"], ctx),
        l_fill_spec=_ctx_style_spec(border_style["l_line"], ctx),
    )

    ctx.container_push(pile, is_new_block=True, custom_add=box)
    ctx.spec_push(utils.spec_from_style(quote_style["style"]))


@contrib_first
def render_blockquote_close(token: Dict, ctx: Context):
    """ """
    ctx.spec_pop()
    ctx.container_pop()


@tutor(
    "markdown",
    "code blocks",
    r"""
    Multi-line code blocks are either surrounded by "fences" (three in a row of
    either `\`` or `~`), or are lines of text indented at least four spaces.

    Fenced codeblocks let you specify the language of the code:

    <TUTOR:EXAMPLE>
    ```python
    def hello_world():
        print("Hello, world!\n")
    ```
    </TUTOR:EXAMPLE>

    ## Style

    The syntax highlighting style used to highlight the code block can be
    specified in the markdown metadata:

    <TUTOR:STYLE>style</TUTOR:STYLE>

    Valid values for the `style` field come directly from pygments. In the
    version of pygments being used as you read this, the list of valid values is:

    {pygments_values}

    > **NOTE** This style name is confusing and will be renamed in lookatme v3.0+
    """.format(
        pygments_values=" ".join(pygments.styles.get_all_styles()),
    ),
)
@contrib_first
def render_fence(token: Dict, ctx: Context):
    """Renders a code block using the Pygments library.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    info = token.get("info", None) or "text"
    lang = info.split()[0]
    # TODO support line highlighting, etc?
    text = token["content"]
    res = pygments_render.render_text(text, lang=lang)

    ctx.widget_add([urwid.Divider(), res, urwid.Divider()])


def _extract_nested_table_tokens(
    tokens: List[Dict],
) -> Tuple[Dict, Dict]:
    idx = 0

    thead_token = None
    tbody_token = None

    parent_token_stack = []
    while idx < len(tokens):
        token = tokens[idx]
        idx += 1

        if re.match(r"(thead|tbody|tr|th|td)_open", token["type"]):
            if parent_token_stack:
                parent = parent_token_stack[-1]
                parent["children"].append(token)
            token["children"] = token.get("children", None) or []
            parent_token_stack.append(token)
            if token["type"] == "thead_open":
                thead_token = token
            elif token["type"] == "tbody_open":
                tbody_token = token

            attrs = token.get("attrs", None)
            if attrs is not None:
                token["attrs"] = dict(attrs)
                style = token["attrs"].get("style", "")
                align = "left"
                if "text-align:center" in style:
                    align = "center"
                elif "text-align:right" in style:
                    align = "right"
                token["align"] = align
        elif re.match(r"(thead|tbody|tr|th|td)_close", token["type"]):
            parent_token_stack.pop()
        else:
            parent = parent_token_stack[-1]
            parent["children"].append(token)

    if thead_token is None:
        raise ValueError("thead must be present!")
    if tbody_token is None:
        raise ValueError("thead must be present!")

    return (thead_token, tbody_token)


@tutor(
    "markdown",
    "tables",
    r"""
    Rows in tables are defined by separating columns with `|` characters. The
    header row is the first row defined and is separated by hypens (`---`).

    Alignment within a column can be set by adding a colon, `:`, to the left,
    right, or both ends of a header's separator.

    <TUTOR:EXAMPLE>
    | left align | centered | right align |
    |------------|:--------:|------------:|
    | 1          |     a    |           A |
    | 11         |    aa    |          AA |
    | 111        |    aaa   |         AAA |
    | 1111       |   aaaaa  |        AAAA |
    </TUTOR:EXAMPLE>

    ## Style

    Tables can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>table</TUTOR:STYLE>
    """,
)
@contrib_first
def render_table_open(token: Dict, ctx: Context):
    """ """
    ctx.ensure_new_block()

    from lookatme.widgets.table import Table

    # TODO: are nested tables even possible without using html? let's ignore
    # that edge case for now and assume we're just looking for the first
    # table_close
    table_children = []
    # consume the tokens until we see a table_close!
    for token in ctx.tokens:
        if token["type"] == "table_close":
            break
        table_children.append(copy.deepcopy(token))

    thead, tbody = _extract_nested_table_tokens(table_children)
    if thead is None or tbody is None:
        raise Exception("thead and tbody must be defined!")

    border_style = config.get_style()["table"]["border"]

    table = Table(header=thead, body=tbody, ctx=ctx)

    box = FancyBox(
        table,
        tl_corner=border_style["tl_corner"]["text"],
        tr_corner=border_style["tr_corner"]["text"],
        br_corner=border_style["br_corner"]["text"],
        bl_corner=border_style["bl_corner"]["text"],
        tl_corner_spec=_ctx_style_spec(border_style["tl_corner"], ctx),
        tr_corner_spec=_ctx_style_spec(border_style["tr_corner"], ctx),
        br_corner_spec=_ctx_style_spec(border_style["br_corner"], ctx),
        bl_corner_spec=_ctx_style_spec(border_style["bl_corner"], ctx),
        t_fill=border_style["t_line"]["text"],
        r_fill=border_style["r_line"]["text"],
        b_fill=border_style["b_line"]["text"],
        l_fill=border_style["l_line"]["text"],
        t_fill_spec=_ctx_style_spec(border_style["t_line"], ctx),
        r_fill_spec=_ctx_style_spec(border_style["r_line"], ctx),
        b_fill_spec=_ctx_style_spec(border_style["b_line"], ctx),
        l_fill_spec=_ctx_style_spec(border_style["l_line"], ctx),
    )

    padding = urwid.Padding(box, width=table.total_width + 2, align="center")
    config.get_log().debug("table total width: {}".format(table.total_width))

    def table_changed(*args, **kwargs):
        padding.width = table.total_width + 2

    urwid.connect_signal(table, "change", table_changed)

    ctx.widget_add(padding)


@contrib_first
def render_hr(token, ctx: Context):
    """Render a newline

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    hrule_style = config.get_style()["hrule"]
    hrule_spec = ctx.spec_text_with(utils.spec_from_style(hrule_style))
    div = urwid.Divider(hrule_style["text"])

    with ctx.use_container(urwid.Pile([]), is_new_block=True):
        ctx.widget_add(urwid.Text(" "))
        ctx.widget_add(urwid.AttrMap(div, hrule_spec))
        ctx.widget_add(urwid.Text(" "))


# @contrib_first
# def render_blankline(token, ctx: Context):
#     """Render a newline
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
#     value descriptions.
#     """
#     return [urwid.Divider()]
#
#
# # @contrib_first
# # def render_hrule(token, ctx: Context):
# #     """Render a newline
# #
# #     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
# #     value descriptions.
# #     """
# #     hrule_conf = config.get_style()["hrule"]
# #     div = urwid.Divider(hrule_conf['char'], top=1, bottom=1)
# #     return urwid.Pile([urwid.AttrMap(div, utils.spec_from_style(hrule_conf['style']))])
#
#
# @contrib_first
# def render_heading(token, ctx: Context):
#     """Render markdown headings, using the defined styles for the styling and
#     prefix/suffix.
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
#     value descriptions.
#
#     Below are the default stylings for headings:
#
#     .. code-block:: yaml
#
#         headings:
#           '1':
#             bg: default
#             fg: '#9fc,bold'
#             prefix: "██ "
#             suffix: ""
#           '2':
#             bg: default
#             fg: '#1cc,bold'
#             prefix: "▓▓▓ "
#             suffix: ""
#           '3':
#             bg: default
#             fg: '#29c,bold'
#             prefix: "▒▒▒▒ "
#             suffix: ""
#           '4':
#             bg: default
#             fg: '#66a,bold'
#             prefix: "░░░░░ "
#             suffix: ""
#           default:
#             bg: default
#             fg: '#579,bold'
#             prefix: "░░░░░ "
#             suffix: ""
#
#     :returns: A list of urwid Widgets or a single urwid Widget
#     """
#     headings = config.get_style()["headings"]
#     level = token["level"]
#     style = config.get_style()["headings"].get(str(level), headings["default"])
#
#     header_spec = utils.spec_from_style(style)
#     with ctx.use_spec(header_spec):
#         prefix_token = {"type": "text", "text": style["prefix"]}
#         suffix_token = {"type": "text", "text": style["suffix"]}
#         markdown_inline.render_all([prefix_token] + token["children"] + [suffix_token], ctx)
#
#     return [urwid.Divider()] + ctx.inline_widgets_consumed + [urwid.Divider()]
#
#
# @contrib_first
# def render_table(token, ctx: Context):
#     """Renders a table using the :any:`Table` widget.
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
#     value descriptions.
#
#     The table widget makes use of the styles below:
#
#     .. code-block:: yaml
#
#         table:
#           column_spacing: 3
#           header_divider: "─"
#
#     :returns: A list of urwid Widgets or a single urwid Widget
#     """
#     from lookatme.widgets.table import Table
#
#     table_header = None
#     table_body = None
#
#     for child_token in token["children"]:
#         if child_token["type"] == "table_head":
#             table_header = child_token
#         elif child_token["type"] == "table_body":
#             table_body = child_token
#         else:
#             raise NotImplementedError("Unsupported table child token: {!r}".format(child_token["type"]))
#
#     table = Table(header=table_header, body=table_body, ctx=ctx)
#     padding = urwid.Padding(table, width=table.total_width + 2, align="center")
#
#     def table_changed(*args, **kwargs):
#         padding.width = table.total_width + 2
#
#     urwid.connect_signal(table, "change", table_changed)
#
#     return padding
#
#
# @contrib_first
# def render_list(token, ctx: Context):
#     """Handles the indentation when starting rendering a new list. List items
#     themselves (with the bullets) are rendered by the
#     :any:`render_list_item_start` function.
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
#     value descriptions.
#     """
#     res = []
#     # Consume any queued inline widgets from previous tokens!
#     res += ctx.inline_widgets_consumed
#
#     list_container = urwid.Pile([])
#
#     level = 1
#     prev_meta = get_meta(ctx.container)
#     in_list = prev_meta.get("is_list", False)
#     if in_list:
#         level = prev_meta["level"] + 1
#
#     meta = get_meta(list_container)
#     meta["is_list"] = True
#     meta["level"] = level
#     meta["ordered"] = token["ordered"]
#     meta["item_count"] = 0
#     meta["list_start_token"] = token
#     meta["max_list_marker_width"] = token.get("max_list_marker_width", 2)
#     meta["ordered"] = token["ordered"]
#
#     with ctx.use_container(list_container):
#         render_all(token["children"], ctx)
#
#     meta = get_meta(list_container)
#     meta["list_start_token"]["max_list_marker_width"] = meta["max_list_marker_width"]
#
#     widgets = []
#     if not in_list:
#         widgets.append(urwid.Divider())
#         widgets.append(ctx.wrap_widget(urwid.Padding(list_container, left=2)))
#         widgets.append(urwid.Divider())
#         return res + widgets
#     return res + [list_container]
#
#
# @contrib_first
# def render_list_item(token, ctx: Context):
#     """Render the start of a list item. This function makes use of two
#     different styles, one each for unordered lists (bullet styles) and ordered
#     lists (numbering styles):
#
#     .. code-block:: yaml
#
#         bullets:
#           '1': "•"
#           '2': "⁃"
#           '3': "◦"
#           default: "•"
#         numbering:
#           '1': "numeric"
#           '2': "alpha"
#           '3': "roman"
#           default: "numeric"
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
#     value descriptions.
#     """
#     meta = get_meta(ctx.container)
#     list_level = meta["level"]
#     curr_count = _inc_item_count(ctx.container)
#     pile = urwid.Pile(urwid.SimpleFocusListWalker([]))
#
#     if meta["ordered"]:
#         numbering = config.get_style()["numbering"]
#         list_marker_type = numbering.get(str(list_level), numbering["default"])
#         sequence = {
#             "numeric": lambda x: str(x),
#             "alpha": lambda x: chr(ord("a") + x - 1),
#             "roman": lambda x: int_to_roman(x),
#         }[list_marker_type]
#         list_marker = sequence(curr_count) + "."
#     else:
#         bullets = config.get_style()["bullets"]
#         list_marker = bullets.get(str(list_level), bullets["default"])
#
#     marker_text = list_marker + " "
#     if len(marker_text) > meta["max_list_marker_width"]:
#         meta["max_list_marker_width"] = len(marker_text)
#     marker_col_width = meta["max_list_marker_width"]
#
#     res = urwid.Columns([
#         (marker_col_width, urwid.Text((ctx.spec_text_with(utils.spec_from_style("bold")), marker_text))),
#         pile,
#     ])
#     res = ctx.wrap_widget(res)
#
#     with ctx.use_container(pile):
#         render_all(token["children"], ctx)
#
#     pile_or_listbox_add(pile, ctx.inline_widgets_consumed)
#
#     return res
#
#
# @contrib_first
# def render_block_text(token, ctx: Context):
#     """Render block text
#     """
#     markdown_inline.render_all(token["children"], ctx)
#     # let the inline render results continue!
#     # return ctx.inline_widgets_consumed
#     return []
#
#
# @contrib_first
# def render_htmlblock(token, ctx: Context):
#     """Render block html
#     """
#     LookatmeHTMLParser(ctx).feed(token["children"])
#     return ctx.inline_widgets_consumed
#
#
# # @contrib_first
# # def render_paragraph(token, ctx: Context):
# #     markdown_inline.render_all(token["children"], ctx)
# #
# #     res = []
# #     if not _is_list(ctx.container):
# #         res.append(urwid.Divider())
# #     res += ctx.inline_widgets_consumed
# #
# #     return res
#
#
# # @contrib_first
# # def render_paragraph_close(token, ctx: Context):
# #     #markdown_inline.render_all(token["children"], ctx)
# #     return [urwid.Divider()]
# #
# # @contrib_first
# # def render_inline(token, ctx: Context):
# #     markdown_inline.render_all(token["children"], ctx)
# #     return ctx.inline_widgets_consumed
# #
# #
# # @contrib_first
# # def render_block_quote(token, ctx: Context):
# #     """
# #
# #     This function makes use of the styles:
# #
# #     .. code-block:: yaml
# #
# #         quote:
# #           top_corner: "┌"
# #           bottom_corner: "└"
# #           side: "╎"
# #           style:
# #             bg: default
# #             fg: italics,#aaa
# #
# #     See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
# #     return value descriptions.
# #     """
# #     pile = urwid.Pile([])
# #
# #     styles = config.get_style()["quote"]
# #
# #     quote_side = styles["side"]
# #     quote_top_corner = styles["top_corner"]
# #     quote_bottom_corner = styles["bottom_corner"]
# #     quote_style = styles["style"]
# #
# #     with ctx.use_container(pile):
# #         with ctx.use_spec(utils.spec_from_style(quote_style)):
# #             for child_token in token["children"]:
# #                 render(child_token, ctx)
# #
# #     # remove leading/trailing divider if they were added to the pile
# #     if isinstance(pile.contents[0][0], urwid.Divider):
# #         pile.contents = pile.contents[1:]
# #     if isinstance(pile.contents[-1][0], urwid.Divider):
# #         pile.contents = pile.contents[:-1]
# #
# #     return [
# #         urwid.LineBox(
# #             urwid.AttrMap(
# #                 urwid.Padding(pile, left=2),
# #                 utils.spec_from_style(quote_style),
# #             ),
# #             lline=quote_side, rline="",
# #             tline=" ", trcorner="", tlcorner=quote_top_corner,
# #             bline=" ", brcorner="", blcorner=quote_bottom_corner,
# #         ),
# #     ]
#
#
# @contrib_first
# def render_block_code(token, ctx: Context):
#     """Renders a code block using the Pygments library.
#
#     See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
#     return value descriptions.
#     """
#     info = token.get("info", None) or "text"
#     lang = info.split()[0]
#     # TODO support line highlighting, etc?
#     text = token["text"]
#     res = pygments_render.render_text(text, lang=lang)
#
#     return [
#         urwid.Divider(),
#         res,
#         urwid.Divider()
#     ]
