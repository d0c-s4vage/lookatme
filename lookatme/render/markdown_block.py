"""
Defines render functions that render lexed markdown block tokens into urwid
representations
"""


import copy
import pygments
import pygments.styles
import pygments.lexers
import re
import sys
from typing import Any, Dict, List, Tuple, Optional, Union

import urwid

import lookatme.config as config
import lookatme.render.markdown_inline as markdown_inline
from lookatme.contrib import contrib_first
from lookatme.render.context import Context
from lookatme.tutorial import tutor
from lookatme.widgets.fancy_box import FancyBox
import lookatme.widgets.codeblock as codeblock
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


def render_all(ctx: Context, and_unwind: bool = False):
    for token in ctx.tokens:
        ctx.log_debug("Rendering block token: {!r}".format(token))
        render(token, ctx)

    if not and_unwind:
        return

    # normally ctx.unwind_tokens will be empty as every "open" token will have
    # a matching "close" token. However, sometimes (like with progressive slides),
    # there will be some tokens missing from the token stream.
    #
    # this is where we artificially close all open tokens
    for unwind_token in ctx.unwind_tokens_consumed:
        ctx.log_debug("Rendering unwind block token: {!r}".format(unwind_token))
        render(unwind_token, ctx)


@tutor(
    "markdown block",
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
    next_token = ctx.tokens.at_offset(0)

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
    with ctx.use_tokens(token.get("children", []), inline=True):
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
    "markdown block",
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
    "markdown block",
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
    "markdown block",
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
    "markdown block",
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
def render_heading_open(token: Dict, ctx: Context):
    """ """
    ctx.ensure_new_block()

    headings = config.get_style()["headings"]
    level = token["level"]
    style = config.get_style()["headings"].get(str(level), headings["default"])

    header_spec = utils.spec_from_style(style)
    ctx.spec_push(header_spec)
    prefix_token = ctx.fake_token("text", content=style["prefix"])
    markdown_inline.render(prefix_token, ctx)


@contrib_first
def render_heading_close(token: Dict, ctx: Context):
    """ """
    headings = config.get_style()["headings"]
    level = int(token["tag"].replace("h", ""))
    style = config.get_style()["headings"].get(str(level), headings["default"])

    suffix_token = ctx.fake_token("text", content=style["suffix"])
    markdown_inline.render(suffix_token, ctx)

    ctx.spec_pop()


@tutor(
    "markdown block",
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


def _parse_hl_lines(values) -> List:
    """Parse comma-separated lists of line ranges to highlight"""
    res = []
    matches = re.finditer(
        r"""
            ,?\s*
            (
                (?P<rangeStart>[0-9]+)
                (\.\.|-)
                (?P<rangeEnd>[0-9]+)
                |
                (?P<singleLine>[0-9]+)
            )
        \s*""",
        values,
        re.VERBOSE,
    )

    for match in matches:
        info = match.groupdict()
        if info["singleLine"]:
            val = int(info["singleLine"])
            res.append(range(val, val + 1))
        elif info["rangeStart"]:
            res.append(
                range(
                    int(info["rangeStart"]),
                    int(info["rangeEnd"]) + 1,
                )
            )

    return res


def _parse_curly_extra(data: str) -> Dict[str, Any]:
    res = {}

    matches = re.finditer(
        r"""\s*
        (
            (?P<attr>[a-zA-Z-_]+)
                \s*=\s*
                (
                    "(?P<doubleQuoteVal>[^"]*)"
                    |
                    '(?P<singleQuoteVal>[^']*)'
                    |
                    (?P<plainVal>[a-zA-Z0-9-_,]+)
                )
            |
            (?P<class>\.)?
            (?P<id>\.)?
            (?P<classOrIdName>[a-zA-Z0-9-_]+)
        )
        \s*
        """,
        data,
        re.VERBOSE,
    )

    for match in matches:
        info = match.groupdict()

        if info["classOrIdName"]:
            val = info["classOrIdName"].lower()
            if val in codeblock.supported_langs():
                res["lang"] = info["classOrIdName"]
            elif val in (
                "numberlines",
                "number_lines",
                "numbers",
                "line_numbers",
                "linenumbers",
                "line_numbers",
            ):
                res["line_numbers"] = True
        elif info["attr"]:
            attr = info["attr"].lower()
            val = info["plainVal"] or info["doubleQuoteVal"] or info["singleQuoteVal"]
            if attr in ("startfrom", "start_from", "line_numberstart", "startlineno"):
                res["start_line_number"] = int(val)
            elif attr in ("hl_lines", "hllines", "highlight", "highlight_lines"):
                res["hl_lines"] = _parse_hl_lines(val)

    return res


@tutor(
    "markdown block",
    "code blocks - extra attributes",
    r"""
    Code blocks can also have additional attributes defined by using curly braces.
    Values within the curly brace are either css class names or ids (start with a `.`
    or `#`), or have the form `key=value`.

    The attributes below have specific meanings - all other attributes will be
    ignored:

    * `.language` - use `language` as the syntax highlighting language
    * `.numberLines` - add line numbers
    * `startFrom=X` - start the line numbers from the line `X`
    * `hllines=ranges` - highlight the line ranges. This should be a comma separated
      list of either single line numbers, or a line range (e.g. `4-5`).

    <TUTOR:EXAMPLE>
    ```{.python .numberLines hllines=4-5,7 startFrom="3"}
    def hello_world():
        print("Hello, world!\n")
        print("Hello, world!\n")
        print("Hello, world!\n")
        print("Hello, world!\n")
        print("Hello, world!\n")
    ```
    </TUTOR:EXAMPLE>
    """,
)
@tutor(
    "markdown block",
    "code blocks",
    r"""
    Multi-line code blocks are either surrounded by "fences" (three in a row of
    either `\`` or `~`), or are lines of text indented at least four spaces.

    Fenced codeblocks let you specify the language of the code. (See the next
    slide about additional attributes)

    <TUTOR:EXAMPLE>
    ```python
    def hello_world():
        print("Hello, world!\n")
    ```
    </TUTOR:EXAMPLE>

    ## Style

    The syntax highlighting style used to highlight the code block can be
    specified in the markdown metadata, as well as an override for the
    background color, and the language to use for inline code.

    <TUTOR:STYLE {{hllines=4,6}}>code</TUTOR:STYLE>

    Valid values for the `style` field come directly from pygments. In the
    version of pygments being used as you read this, the list of valid values is:

    {pygments_values}
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
    ctx.ensure_new_block()

    info = token.get("info", None) or "text"

    match = re.match(r"^(?P<lang>[^{\s]+)?\s*(\{(?P<curly_extra>[^{]+)\})?", info)
    lang = "text"
    line_numbers = False
    start_line_number = 1
    hl_lines = []

    if match is not None:
        full_info = match.groupdict()
        if full_info["lang"] is not None:
            lang = full_info["lang"]
        if full_info["curly_extra"] is not None:
            curly_extra = _parse_curly_extra(full_info["curly_extra"])
            lang = curly_extra.get("lang", lang)
            line_numbers = curly_extra.get("line_numbers", line_numbers)
            start_line_number = curly_extra.get("start_line_number", start_line_number)
            hl_lines = curly_extra.get("hl_lines", [])

    curr_spec = ctx.spec_text
    default_fg = "default"
    bg_override = config.get_style()["code"]["bg_override"]
    if curr_spec:
        default_fg = (
            default_fg
            or utils.overwrite_style({"fg": curr_spec.foreground}, {"fg": default_fg})[
                "fg"
            ]
        )

    code = codeblock.CodeBlock(
        source=token["content"],
        lang=lang,
        style_name=config.get_style()["code"]["style"],
        line_numbers=line_numbers,
        start_line_number=start_line_number,
        hl_lines=hl_lines,
        default_fg=default_fg,
        bg_override=bg_override,
    )

    ctx.widget_add(code)


#
#    text = token["content"]
#    res = pygments_render.render_text(
#        text,
#        lang=lang,
#        line_numbers=line_numbers,
#        start_line_number=start_line_number,
#        hl_lines=hl_lines,
#    )
#
#    ctx.widget_add(res)


class TableTokenExtractor:
    def __init__(self):
        self.root = {"children": []}
        self.parent_token_stack = [self.root]
        self.thead_token = None
        self.tbody_token = None

    @property
    def curr_parent(self) -> Dict:
        return self.parent_token_stack[-1]

    @property
    def curr_siblings(self) -> List[Dict]:
        parent = self.curr_parent
        siblings = parent.get("children", [])
        if not isinstance(siblings, list):
            siblings = parent["children"] = []
        return siblings

    def is_table_element_open(self, token: Dict) -> bool:
        ttype = token["type"]
        return re.match(r"(thead|tbody|tr|th|td)_open", ttype) is not None

    def is_table_element_close(self, token: Dict) -> bool:
        ttype = token["type"]
        return re.match(r"(thead|tbody|tr|th|td)_close", ttype) is not None

    def set_token_alignment(self, token: Dict):
        attrs = token.get("attrs", None)
        if attrs is None:
            align = "left"
        else:
            token["attrs"] = dict(attrs)
            style = token["attrs"].get("style", "")
            align = "left"
            if "text-align:center" in style:
                align = "center"
            elif "text-align:right" in style:
                align = "right"
            token["align"] = align

    def process_tokens(
        self, tokens: List[Dict]
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        for token in tokens:
            self.process_token(token)

        return self.thead_token, self.tbody_token

    def process_token(self, token: Dict):
        if self.is_table_element_open(token):
            self.curr_siblings.append(token)
            self.parent_token_stack.append(token)

            if token["type"] == "thead_open":
                self.thead_token = token
            elif token["type"] == "tbody_open":
                self.tbody_token = token

            self.set_token_alignment(token)
        elif self.is_table_element_close(token):
            self.parent_token_stack.pop()
        else:
            self.curr_siblings.append(token)


def _is_tag_close_with_tag_open_before_line(
    token: Dict, line_num: int, ctx: Context
) -> bool:
    if token["type"] != "inline":
        return False
    if len(token["children"]) != 1:
        return False

    inline_child = token["children"][0]
    if inline_child["type"] != "html_inline":
        return False

    if not inline_child["content"].startswith("</"):
        return False

    # now to see where the current tag open started!
    if ctx.tag_token["map"][0] < line_num:
        return True

    return False


@tutor(
    "markdown block",
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

    table_start_line = token["map"][0]

    # TODO: are nested tables even possible without using html? let's ignore
    # that edge case for now and assume we're just looking for the first
    # table_close
    table_children = []
    saw_table_close = False
    to_inject = None
    unwind_bookmark = ctx.unwind_bookmark

    # consume the tokens until we see a table_close!
    for idx, table_token in enumerate(ctx.tokens):
        if _is_tag_close_with_tag_open_before_line(table_token, table_start_line, ctx):
            # we still have to process the close tag!
            to_inject = table_token

            # undo the current td and tr and consume the next two tokens as
            # well
            utils.check_token_type(table_children.pop(), "td_open")
            utils.check_token_type(table_children.pop(), "tr_open")

            # the markdown parser will add empty td_open/inline/close tokens
            # for the number of columns in the table - need to consume and
            # ignore all of these
            for next_token in ctx.tokens:
                if next_token["type"] in ("td_close", "td_open", "inline"):
                    continue
                utils.check_token_type(next_token, "tr_close")
                break
            break

        table_children.append(copy.deepcopy(table_token))
        if table_token["type"] == "table_close":
            saw_table_close = True
            break

    if not saw_table_close:
        # don't consume them yet! We may still have to iterate through more
        # tokens in the next for loop in case we bailed out of the table
        # early b/c of an html element
        table_children += list(ctx.unwind_tokens_from(unwind_bookmark))

        # we may break early if we find a an html element that was started
        # before the table but somehow ended within the table. In that case,
        # we still need to consume the rest of the table tokens (but discard
        # them).
        for token in ctx.tokens:
            if token["type"] == "table_close":
                break

        _ = ctx.unwind_tokens_consumed

    if to_inject:
        token_iter = ctx.tokens
        token_iter.tokens.insert(token_iter.idx, to_inject)

    extractor = TableTokenExtractor()
    extractor.process_tokens(table_children)
    thead = extractor.thead_token
    tbody = extractor.tbody_token
    if thead is None:
        raise Exception("At least thead must be defined for tables")

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
