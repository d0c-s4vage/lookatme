"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import re
import sys
from typing import Dict, Optional

import urwid

import lookatme.config as config
import lookatme.utils as utils
from lookatme.contrib import contrib_first
from lookatme.render.context import Context
from lookatme.render.markdown_html import Tag
from lookatme.tutorial import tutor
from lookatme.widgets.clickable_text import LinkIndicatorSpec
import lookatme.widgets.codeblock as codeblock


THIS_MOD = sys.modules[__name__]


def markdown_block():
    import lookatme.render.markdown_block as markdown_block

    return markdown_block


def render(token, ctx: Context):
    """Render an inline token[""] These tokens come from "children" tokens of
    a block token[""]
    """
    with ctx.level_inc():
        token_type = token["type"].lower()
        fn = getattr(THIS_MOD, "render_{}".format(token_type), None)
        if fn is None:
            raise ValueError("Token type {!r} is not yet supported".format(token_type))
        return fn(token, ctx)


def render_all(ctx: Context, and_unwind: bool = False):
    for token in ctx.tokens:
        ctx.log_debug("Rendering inline token: {!r}".format(token))
        render(token, ctx)

    if not and_unwind:
        return

    # normally ctx.unwind_tokens will be empty as every "open" token will have
    # a matching "close" token. However, sometimes (like with progressive slides),
    # there will be some tokens missing from the token stream.
    #
    # this is where we artificially close all open tokens
    for unwind_token in ctx.unwind_tokens:
        ctx.log_debug("Rendering unwind block token: {!r}".format(unwind_token))
        render(unwind_token, ctx)


# -------------------------------------------------------------------------


@contrib_first
def render_text(token, ctx: Context):
    ctx.inline_push((ctx.spec_text, token.get("content", "")))


@tutor(
    "markdown inline",
    "emphasis",
    r"""
    <TUTOR:EXAMPLE>
    The donut jumped *under* the crane.
    </TUTOR:EXAMPLE>

    ## Style

    Emphasis can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>emphasis</TUTOR:STYLE>
    """,
)
@contrib_first
def render_em_open(_, ctx: Context):
    spec = utils.spec_from_style(config.get_style()["emphasis"])
    ctx.spec_push(spec)


@contrib_first
def render_em_close(_, ctx: Context):
    ctx.spec_pop()


@tutor(
    "markdown inline",
    "strong emphasis",
    r"""
    <TUTOR:EXAMPLE>
    They jumped **over** the wagon
    </TUTOR:EXAMPLE>

    ## Style

    Strong emphasis can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>strong_emphasis</TUTOR:STYLE>
    """,
)
@contrib_first
def render_strong_open(_, ctx: Context):
    spec = utils.spec_from_style(config.get_style()["strong_emphasis"])
    ctx.spec_push(spec)


@contrib_first
def render_strong_close(_, ctx: Context):
    ctx.spec_pop()


@tutor(
    "markdown inline",
    "strikethrough",
    r"""
    <TUTOR:EXAMPLE>
    I lost my ~~mind~~ keyboard and couldn't type anymore.
    </TUTOR:EXAMPLE>

    ## Style

    Strikethrough can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>strikethrough</TUTOR:STYLE>
    """,
)
@contrib_first
def render_s_open(_, ctx: Context):
    spec = utils.spec_from_style(config.get_style()["strikethrough"])
    ctx.spec_push(spec)


@contrib_first
def render_s_close(_, ctx: Context):
    ctx.spec_pop()


@tutor(
    "markdown inline",
    "links",
    r"""
    Links are inline elements in markdown and have the form `[text](link)`

    <TUTOR:EXAMPLE>
    [lookatme on GitHub](https://github.com/d0c-s4vage/lookatme)
    </TUTOR:EXAMPLE>

    ## Style

    Links can be styled with slide metadata. This is the default style:

    <TUTOR:STYLE>link</TUTOR:STYLE>
    """,
)
@contrib_first
def render_link_open(token, ctx: Context):
    attrs = dict(token["attrs"])
    href = attrs.get("href", "")

    plain_spec = utils.spec_from_style(config.get_style()["link"])
    ctx.spec_push(LinkIndicatorSpec(href, plain_spec, link_type="link"))


@contrib_first
def render_link_close(_, ctx: Context):
    ctx.spec_pop()


@tutor(
    "markdown inline",
    "images",
    r"""
    Vanilla lookatme renders images as links. Some extensions provide ways to
    render images in the terminal.

    Consider exploring:

    * [lookatme.contrib.image_ueberzug](https://github.com/d0c-s4vage/lookatme.contrib.image_ueberzug)
      * This works on Linux only, with X11, and must be separately installed

    <TUTOR:EXAMPLE>
    ![image alt](https://image/url)
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_image(token, ctx: Context):
    attrs = dict(token["attrs"])
    attrs["href"] = attrs.get("src", "")

    fake_token = ctx.fake_token("link_open", attrs=list(attrs.items()))
    render_link_open(fake_token, ctx)
    ctx.spec_peek().link_type = "image"
    with ctx.use_tokens(token["children"]):
        render_all(ctx)
    fake_token = ctx.fake_token("link_close", attrs=list(attrs.items()))
    render_link_close(fake_token, ctx)


@contrib_first
def render_image_close(token, ctx: Context):
    return render_link_close(token, ctx)


def _prev_token_is_html(ctx: Context) -> bool:
    prev = ctx.tokens.at_offset(-1)
    if not prev:
        return False
    return prev["type"] == "html_inline"


def _next_token_is_html_close(ctx: Context) -> bool:
    next_token = ctx.tokens.peek()
    if not next_token:
        return False
    return next_token["type"] == "html_inline" and next_token["content"].startswith(
        "</"
    )


@contrib_first
def render_hardbreak(_, ctx: Context):
    ctx.inline_push((ctx.spec_text, "\n"))


@contrib_first
def render_softbreak(_, ctx: Context):
    # do not add spaces between HTML tags!
    if _prev_token_is_html(ctx):
        return
    if _next_token_is_html_close(ctx):
        return

    markup = ctx.get_inline_markup()
    # if the previous line ended with a dash, don't add a space!
    if len(markup) > 0:
        prev_markup = markup[-1]
        if isinstance(prev_markup, str):
            prev_text = prev_markup
        elif isinstance(prev_markup, tuple) and len(prev_markup) == 2:
            prev_text = prev_markup[1]
        else:
            raise Exception("Unknown condition handling softbreak")

        # if the previous text was a dash-split, then don't add a space
        if re.match(r".*[^\s]-$", prev_text.split("\n")[-1]) is not None:
            return

    ctx.inline_push((ctx.spec_text, " "))


@tutor(
    "markdown inline",
    "inline code",
    r"""
    <TUTOR:EXAMPLE>
    The `OddOne` class accepts `Table` instances, converts them to raw pointers,
    forces garbage collection to run.
    </TUTOR:EXAMPLE>

    ## Style

    The default language used for syntax highlighting of inline code blocks
    can be controlled through the markdown metadata. See the
    `styles.code.inline_lang` option:

    <TUTOR:STYLE {hllines=5}>code</TUTOR:STYLE>
    """,
)
@contrib_first
def render_code_inline(token, ctx: Context):
    inline_lang = config.get_style()["code"]["inline_lang"]
    code_style = config.get_style()["code"]["style"]

    default_fg = "default"
    bg_override = config.get_style()["code"]["bg_override"]
    curr_spec = ctx.spec_text
    if curr_spec:
        default_fg = (
            default_fg
            or utils.overwrite_style({"fg": curr_spec.foreground}, {"fg": default_fg})[
                "fg"
            ]
        )

    lexer = codeblock.get_lexer(inline_lang)
    style = codeblock.get_style_cache(
        default_fg=default_fg, bg_override=bg_override
    ).get_style(code_style)

    tokens = list(lexer.get_tokens(token["content"]))
    # split the tokens into distinct lines, and only keep the first line
    # of tokens
    tokens = codeblock.tokens_to_lines(tokens)[0]

    markups = codeblock.tokens_to_markup(tokens, style)  # type: ignore

    for spec, text in markups:
        spec = ctx.spec_text_with(spec)
        ctx.inline_push((spec, text))


@tutor(
    "markdown inline",
    "html tags",
    r"""
    Many markdown renderers support a limited set of inline html. So does
    lookatme!

    Lookatme current supports these tags:

    |       tag | note                                                    |
    |----------:|---------------------------------------------------------|
    |   `<div>` | Wrap block elements, set background color, etc.         |
    |     `<u>` | Underline text                                          |
    |     `<i>` | Italicize text                                          |
    |     `<b>` | Bold text                                               |
    |    `<em>` | "em" for emphasis - in lookatme this inverts the colors |
    | `<blink>` | Make the text blink (not all terminals support this)    |
    |    `<br>` | Force a newline                                         |
    |    `<ul>` | Begin an unordered list                                 |
    |    `<ol>` | Begin an ordered list                                   |
    |    `<li>` | List item element                                       |
    |   `<???>` | Treated as an inline element                            |

    Note that all unrecognized tags (including `<span>`) will be treated as
    inline elements. Style attributes will work, but a new block element
    will not be created as is done with `<div>`s.

    Each tag supports the `style` attribute features below:

    * `color` - foreground color of the text (`#RRGGBB`)
    * `background-color` - background color of the text (`#RRGGBB`)
    * `text-decoration: underline` - underline the text
    * `font-weight: bold` - bold the text
    * `font-style: italic` - italicize the text

    See the following slides for specifics and examples of each html element.
    """,
)
@contrib_first
def render_html_inline(token, ctx: Context):
    tags = Tag.parse(token["content"])

    for tag in tags:
        if tag.is_open:
            fn_name = "render_html_tag_{}_open".format(tag.name)
            default = render_html_tag_default_open
        else:
            fn_name = "render_html_tag_{}_close".format(tag.name)
            default = render_html_tag_default_close

        fn = getattr(THIS_MOD, fn_name, None)
        if fn is None:
            fn = default

        style_spec = None
        if len(tag.style) > 0:
            fg = [tag.style.get("color", "")]
            if "underline" in tag.style.get("text-decoration", ""):
                fg.append("underline")
            if "line-through" in tag.style.get("text-decoration", ""):
                fg.append("strikethrough")
            if "bold" in tag.style.get("font-weight", ""):
                fg.append("bold")
            if "italic" in tag.style.get("font-style", ""):
                fg.append("italics")

            style_spec = utils.spec_from_style(
                {
                    "fg": ",".join(fg),
                    "bg": tag.style.get("background-color", ""),
                }
            )

        fn(token, tag, ctx, style_spec)


@contrib_first
def render_html_tag_default_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_push(tag.name, token, style_spec)


@contrib_first
def render_html_tag_default_close(
    _, _tag: Tag, ctx: Context, _style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_pop()


@tutor(
    "markdown inline",
    "html tag `<u>`",
    r"""
    The `<u>` tag can be used to underline all elements within it:

    <TUTOR:EXAMPLE>
    I <u>made</u> too

    <u>
    * much
        * pasta
    </u>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_u_open(
    token, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("underline"))
    ctx.tag_push(tag.name, token, style_spec, text_only_spec=True)


@tutor(
    "markdown inline",
    "html tag `<i>`",
    r"""
    The `<i>` tag can be used to italicize all elements within it:

    <TUTOR:EXAMPLE>
    <i>but</i> I was so

    <i>
    | hungry | there's none |
    |--------|--------------|
    | left   | for you      |
    </i>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_i_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("italics"))
    ctx.tag_push(tag.name, token, style_spec)


@tutor(
    "markdown inline",
    "html tag `<b>`",
    r"""
    The `<b>` tag can be used to bold all elements within it:

    <TUTOR:EXAMPLE>
    so I made m<b>ore lasagna</b>

    <b>
    > just for fun
    </b>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_b_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("bold"))
    ctx.tag_push(tag.name, token, style_spec)


@tutor(
    "markdown inline",
    "html tag `<em>`",
    r"""
    The `<em>` tag can be used to emphasize all elements within it. In
    lookatme this results in inverted colors

    <TUTOR:EXAMPLE>
    I j<em>us</em>t <em>n</em>E<em>E</em>d butter<em>!</em>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_em_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("standout"))
    ctx.tag_push(tag.name, token, style_spec, text_only_spec=True)


@tutor(
    "markdown inline",
    "html tag `<blink>`",
    r"""
    The `<blink>` tag causes all contents to blink. Not all terminals
    support this.

    <TUTOR:EXAMPLE>
    Can you <blink>hear me</blink> now?

    <blink>
    > YES.
    > We can hear you.
    </blink>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_blink_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("blink"))
    ctx.tag_push(tag.name, token, style_spec)


@tutor(
    "markdown inline",
    "html tag `<br>`",
    r"""
    The `<br>` inserts a newline wherever it's at. This can be especially
    useful in tables!

    <TUTOR:EXAMPLE>
    Newline inserted<br/>here.

    | table                     | of data                   |
    |---------------------------|---------------------------|
    | line1<br/>line2<br/>line3 | single item               |
    | single item               | line1<br/>line2<br/>line3 |
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_br_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_push(tag.name, token, style_spec)
    ctx.inline_push((ctx.spec_text, "\n"))


@tutor(
    "markdown inline",
    "html tag `<div>`",
    r"""
    The `<div>` tag creates a new visual block. `<div>` tags are also the
    best option for setting the background color of entire elements:

    <TUTOR:EXAMPLE>
    <div>text1</div><div>text2</div>

    <div style="background-color: #808020">
    | table       | of data     |
    |-------------|-------------|
    | data        | single item |
    | single item | data        |
    </div>
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_div_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.ensure_new_block()
    ctx.container_push(urwid.Pile([]), is_new_block=True)
    ctx.tag_push(tag.name, token, style_spec)


@contrib_first
def render_html_tag_div_close(
    _, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_pop()
    ctx.container_pop()


@tutor(
    "markdown inline",
    "html tag `<ol>`",
    r"""
    The `<ol>` tag creates a new ordered list. Each child `<li>` element will
    be turned into an ordered item in the list.

    Using `<ol>` is especially handy if you want to embed a list into
    a table cell!

    <TUTOR:EXAMPLE>
    <ol><li>item1</li><li>item2</li></ol>

    | table                                         | with list  |
    |-----------------------------------------------|------------|
    | <ol><li>item in table</li><li>item2</li></ol> | other data |
    | cell                                          | data       |
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_ol_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_push(tag.name, token, style_spec)
    fake_token = ctx.fake_token("ordered_list_open")
    markdown_block().render_ordered_list_open(fake_token, ctx)


@contrib_first
def render_html_tag_ol_close(
    _, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_pop()
    fake_token = ctx.fake_token("ordered_list_close")
    markdown_block().render_ordered_list_close(fake_token, ctx)


@tutor(
    "markdown inline",
    "html tag `<ul>`",
    r"""
    The `<ul>` tag creates a new *un*ordered list. Each child `<li>` element will
    be turned into an item in the list.

    Using `<ul>` is especially handy if you want to embed a list into
    a table cell!

    <TUTOR:EXAMPLE>
    <ul><li>item1</li><li>item2</li></ul>

    | table                                         | with list  |
    |-----------------------------------------------|------------|
    | <ul><li>item in table</li><li>item2</li></ul> | other data |
    | cell                                          | data       |
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_ul_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_push(tag.name, token, style_spec)
    fake_token = ctx.fake_token("bullet_list_open")
    markdown_block().render_bullet_list_open(fake_token, ctx)


@contrib_first
def render_html_tag_ul_close(
    _, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.tag_pop()
    fake_token = ctx.fake_token("bullet_list_close")
    markdown_block().render_bullet_list_close(fake_token, ctx)


@tutor(
    "markdown inline",
    "html tag `<li>`",
    r"""
    The `<li>` tag creates a single list element for both ordered (`<ol>`) and
    unordered (`<ul>`) lists. When not used as a child of an `<ol>` or `<ul>`
    tag, the list item will be assumed to be an unordered list item.

    <TUTOR:EXAMPLE>
    <ol><li>item1</li><li>item2</li></ol>

    Or without the `<ol>`:

    <li>test</li><li>test2</li>

    | table                                | with list  |
    |--------------------------------------|------------|
    | <li>item in table</li><li>item2</li> | other data |
    | cell                                 | data       |
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_html_tag_li_open(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    # if we're not within a ul or ol element, then we need to force one of
    # those to be rendered first
    if (
        not ctx.tokens.unwind_has_type("bullet_list_close")
        and not ctx.tokens.unwind_has_type("ordered_list_close")
        and not ctx.tag_is_ancestor("ol")
        and not ctx.tag_is_ancestor("ul")
    ):
        ctx.log_debug("rendering bullet list open")
        fake_token = ctx.fake_token("bullet_list_open")
        fake_parent_ul = token.setdefault("fake_parent_ul", fake_token)
        markdown_block().render_bullet_list_open(fake_parent_ul, ctx)

    ctx.log_debug("rendering li open")
    ctx.tag_push(tag.name, token, style_spec)
    fake_token = ctx.fake_token("list_item_open")
    li_token = token.setdefault("translated_li_token", fake_token)
    markdown_block().render_list_item_open(li_token, ctx)


@contrib_first
def render_html_tag_li_close(
    token: Dict, tag: Tag, ctx: Context, style_spec: Optional[urwid.AttrSpec]
):
    ctx.log_debug("rendering li close")
    ctx.tag_pop()
    fake_token = ctx.fake_token("list_item_close")
    li_token = token.setdefault("translated_li_token", fake_token)
    markdown_block().render_list_item_close(li_token, ctx)

    # if the next token isn't an ol or ul token, then we need to end this
    # current <li> list
    next_token = ctx.tokens.peek()
    if not next_token or (
        next_token["type"] == "html_inline"
        and next_token["content"] not in ("</ul>", "</ol>", "</li>", "<li>")
        and next_token["type"] != "list_item_open"
    ):
        ctx.log_debug("rendering bullet list close")
        fake_token = ctx.fake_token("bullet_list_close")
        markdown_block().render_bullet_list_close(fake_token, ctx)
