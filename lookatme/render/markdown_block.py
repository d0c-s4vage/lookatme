"""
Defines render functions that render lexed markdown block tokens into urwid
representations
"""


import mistune
import pygments
import pygments.styles
import urwid

import lookatme.config as config
import lookatme.render.markdown_inline as markdown_inline_renderer
import lookatme.render.pygments as pygments_render
import lookatme.utils as utils
from lookatme.contrib import contrib_first
from lookatme.tutorial import tutor
from lookatme.widgets.clickable_text import ClickableText


def _meta(item):
    if not hasattr(item, "meta"):
        meta = {}
        setattr(item, "meta", meta)
    else:
        meta = getattr(item, "meta")
    return meta


def _set_is_list(item, level=1, ordered=False):
    _meta(item).update({
        "is_list": True,
        "list_level": level,
        "ordered": ordered,
        "item_count": 0,
    })


def _inc_item_count(item):
    _meta(item)["item_count"] += 1
    return _meta(item)["item_count"]


def _is_list(item):
    return _meta(item).get("is_list", False)


def _list_level(item):
    return _meta(item).get("list_level", 1)


@contrib_first
def render_newline(token, body, stack, loop):
    """Render a newline

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    return urwid.Divider()


@contrib_first
def render_hrule(token, body, stack, loop):
    """Render a newline

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    hrule_conf = config.get_style()["hrule"]
    div = urwid.Divider(hrule_conf['char'], top=1, bottom=1)
    return urwid.Pile([urwid.AttrMap(div, utils.spec_from_style(hrule_conf['style']))])


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
def render_heading(token, body, stack, loop):
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
    headings = config.get_style()["headings"]
    level = token["level"]
    style = config.get_style()["headings"].get(str(level), headings["default"])

    prefix = utils.styled_text(style["prefix"], style)
    suffix = utils.styled_text(style["suffix"], style)

    rendered = render_text(text=token["text"])
    if len(rendered) > 0:
        rendered = rendered[0]

    return [
        urwid.Divider(),
        ClickableText(
            [prefix] + utils.styled_text(rendered, style) + [suffix]),  # type: ignore
        urwid.Divider(),
    ]


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
def render_table(token, body, stack, loop):
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

    headers = token["header"]
    aligns = token["align"]
    cells = token["cells"]

    table = Table(cells, headers=headers, aligns=aligns)
    padding = urwid.Padding(table, width=table.total_width + 2, align="center")

    def table_changed(*args, **kwargs):
        padding.width = table.total_width + 2

    urwid.connect_signal(table, "change", table_changed)

    return padding


@contrib_first
def render_list_start(token, body, stack, loop):
    """Handles the indentation when starting rendering a new list. List items
    themselves (with the bullets) are rendered by the
    :any:`render_list_item_start` function.

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    res = urwid.Pile([])

    in_list = _is_list(stack[-1])
    list_level = 1
    if in_list:
        list_level = _list_level(stack[-1]) + 1
    _set_is_list(res, list_level, ordered=token['ordered'])
    _meta(res)['list_start_token'] = token
    _meta(res)['max_list_marker_width'] = token.get('max_list_marker_width', 2)
    stack.append(res)

    widgets = []
    if not in_list:
        widgets.append(urwid.Divider())
        widgets.append(urwid.Padding(res, left=2))
        widgets.append(urwid.Divider())
        return widgets
    return res


@contrib_first
def render_list_end(token, body, stack, loop):
    """Pops the pushed ``urwid.Pile()`` from the stack (decreases indentation)

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    meta = _meta(stack[-1])
    meta['list_start_token']['max_list_marker_width'] = meta['max_list_marker_width']
    stack.pop()


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
    """
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
    """
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
    """
)
def _list_item_start(token, body, stack, loop):
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
    list_level = _list_level(stack[-1])
    curr_count = _inc_item_count(stack[-1])
    pile = urwid.Pile(urwid.SimpleFocusListWalker([]))

    meta = _meta(stack[-1])

    if meta["ordered"]:
        numbering = config.get_style()["numbering"]
        list_marker_type = numbering.get(str(list_level), numbering["default"])
        sequence = {
            "numeric": lambda x: str(x),
            "alpha": lambda x: chr(ord("a") + x - 1),
            "roman": lambda x: utils.int_to_roman(x),
        }[list_marker_type]
        list_marker = sequence(curr_count) + "."
    else:
        bullets = config.get_style()["bullets"]
        list_marker = bullets.get(str(list_level), bullets["default"])

    marker_text = list_marker + " "
    if len(marker_text) > meta["max_list_marker_width"]:
        meta["max_list_marker_width"] = len(marker_text)
    marker_col_width = meta["max_list_marker_width"]

    res = urwid.Text(("bold", marker_text))
    res = urwid.Columns([
        (marker_col_width, urwid.Text(("bold", marker_text))),
        pile,
    ])
    stack.append(pile)
    return res


@contrib_first
def render_list_item_start(token, body, stack, loop):
    """Render the start of a list item. This function makes use of the styles:

    .. code-block:: yaml

        bullets:
          '1': "•"
          '2': "⁃"
          '3': "◦"
          default: "•"

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    return _list_item_start(token, body, stack, loop)


@contrib_first
def render_loose_item_start(token, body, stack, loop):
    """Render the start of a list item. This function makes use of the styles:

    .. code-block:: yaml

        bullets:
          '1': "•"
          '2': "⁃"
          '3': "◦"
          default: "•"

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    return _list_item_start(token, body, stack, loop)


@contrib_first
def render_list_item_end(token, body, stack, loop):
    """Pops the pushed ``urwid.Pile()`` from the stack (decreases indentation)

    See :any:`lookatme.tui.SlideRenderer.do_render` for argument and return
    value descriptions.
    """
    stack.pop()


@contrib_first
def render_text(token=None, body=None, stack=None, loop=None, text=None):
    """Renders raw text. This function uses the inline markdown lexer
    from mistune with the :py:mod:`lookatme.render.markdown_inline` render module
    to render the lexed inline markup to a list composed of widgets or
    `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_.
    The created list of widgets/Text markup is then used to create and return
    a list composed entirely of widgets and :any:`ClickableText` instances.

    Many other functions call this function directly, passing in the extra
    ``text`` argument and leaving all other arguments blank.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    if text is None and token is not None:
        text = token["text"]

    inline_lexer = mistune.InlineLexer(markdown_inline_renderer)
    res = inline_lexer.output(text)
    if len(res) == 0:
        res = [""]

    widget_list = []
    curr_text_spec = []
    for item in res:
        if isinstance(item, urwid.Widget):
            if len(curr_text_spec) > 0:
                widget_list.append(ClickableText(curr_text_spec))
                curr_text_spec = []
            widget_list.append(item)
        else:
            curr_text_spec.append(item)
    if len(curr_text_spec) > 0:
        widget_list.append(ClickableText(curr_text_spec))

    return widget_list


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
def render_paragraph(token, body, stack, loop):
    """Renders the provided text with additional pre and post paddings.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    token["text"] = token["text"].replace("\r\n", " ").replace("\n", " ")
    res = render_text(token, body, stack, loop)
    return [urwid.Divider()] + res + [urwid.Divider()]


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
    """
)
@contrib_first
def render_block_quote_start(token, body, stack, loop):
    """Begins rendering of a block quote. Pushes a new ``urwid.Pile()`` to the
    stack that is indented, has styling applied, and has the quote markers
    on the left.

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
    stack.append(pile)

    styles = config.get_style()["quote"]

    quote_side = styles["side"]
    quote_top_corner = styles["top_corner"]
    quote_bottom_corner = styles["bottom_corner"]
    quote_style = styles["style"]

    return [
        urwid.Divider(),
        urwid.LineBox(
            urwid.AttrMap(
                urwid.Padding(pile, left=2),
                utils.spec_from_style(quote_style),
            ),
            lline=quote_side, rline="",
            tline=" ", trcorner="", tlcorner=quote_top_corner,
            bline=" ", brcorner="", blcorner=quote_bottom_corner,
        ),
        urwid.Divider(),
    ]


@contrib_first
def render_block_quote_end(token, body, stack, loop):
    """Pops the block quote start ``urwid.Pile()`` from the stack, taking
    future renderings out of the block quote styling.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    pile = stack.pop()

    # remove leading/trailing divider if they were added to the pile
    if isinstance(pile.contents[0][0], urwid.Divider):
        pile.contents = pile.contents[1:]
    if isinstance(pile.contents[-1][0], urwid.Divider):
        pile.contents = pile.contents[:-1]


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
    )
)
@contrib_first
def render_code(token, body, stack, loop):
    """Renders a code block using the Pygments library.

    See :any:`lookatme.tui.SlideRenderer.do_render` for additional argument and
    return value descriptions.
    """
    lang = token.get("lang", "text") or "text"
    text = token["text"]
    res = pygments_render.render_text(text, lang=lang)

    return [
        urwid.Divider(),
        res,
        urwid.Divider()
    ]
