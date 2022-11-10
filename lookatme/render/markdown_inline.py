"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import re
import sys
from typing import Union

import urwid

import lookatme.config as config
import lookatme.render.pygments as pygments_render
import lookatme.utils as utils
from lookatme.contrib import contrib_first
from lookatme.render.context import Context
from lookatme.render.markdown_html import Tag
from lookatme.tutorial import tutor
from lookatme.widgets.clickable_text import LinkIndicatorSpec

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


def render_all(ctx: Context):
    for token in ctx.tokens:
        ctx.log_debug("Rendering inline token: {!r}".format(token))
        render(token, ctx)

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
    "markdown",
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
    "markdown",
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
    "markdown",
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
    "markdown",
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
    ctx.spec_push(LinkIndicatorSpec(href, plain_spec))


@contrib_first
def render_link_close(_, ctx: Context):
    ctx.spec_pop()


@tutor(
    "markdown",
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

    render_link_open({"type": "image_open", "attrs": list(attrs.items())}, ctx)
    with ctx.use_tokens(token["children"]):
        render_all(ctx)
    render_link_close({}, ctx)


@contrib_first
def render_image_close(token, ctx: Context):
    return render_link_close(token, ctx)


@contrib_first
def render_softbreak(_, ctx: Context):
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
    "markdown",
    "inline code",
    r"""
    <TUTOR:EXAMPLE>
    The `OddOne` class accepts `Table` instances, converts them to raw pointers,
    forces garbage collection to run.
    </TUTOR:EXAMPLE>
    """,
)
@contrib_first
def render_code_inline(token, ctx: Context):
    # TODO: add a style for the default programming language for inline text
    # blocks
    spec, text = pygments_render.render_text(token["content"], plain=True)[0]
    with ctx.use_spec(spec):
        ctx.inline_push((ctx.spec_text, text))


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
            if "underscore" in tag.style.get("text-decoration", ""):
                fg.append("underline")
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
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_push(tag.name, style_spec)


@contrib_first
def render_html_tag_default_close(
    _, _tag: Tag, ctx: Context, _style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_pop()


@contrib_first
def render_html_tag_u_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("underline"))
    ctx.tag_push(tag.name, style_spec, text_only_spec=True)


@contrib_first
def render_html_tag_i_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("italics"))
    ctx.tag_push(tag.name, style_spec)


@contrib_first
def render_html_tag_b_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("bold"))
    ctx.tag_push(tag.name, style_spec)


@contrib_first
def render_html_tag_em_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("standout"))
    ctx.tag_push(tag.name, style_spec, text_only_spec=True)


@contrib_first
def render_html_tag_blink_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    style_spec = utils.overwrite_spec(style_spec, utils.spec_from_style("blink"))
    ctx.tag_push(tag.name, style_spec)


@contrib_first
def render_html_tag_br_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_push(tag.name, style_spec)
    ctx.inline_push((ctx.spec_text, "\n"))


@contrib_first
def render_html_tag_div_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.ensure_new_block()
    ctx.container_push(urwid.Pile([]), is_new_block=True)
    ctx.tag_push(tag.name, style_spec)


@contrib_first
def render_html_tag_div_close(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.container_pop()
    ctx.tag_pop()


@contrib_first
def render_html_tag_ol_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_push(tag.name, style_spec)
    markdown_block().render_ordered_list_open({"type": "ordered_list_open"}, ctx)


@contrib_first
def render_html_tag_ol_close(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_pop()
    markdown_block().render_ordered_list_close({"type": "ordered_list_close"}, ctx)


@contrib_first
def render_html_tag_ul_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_push(tag.name, style_spec)
    markdown_block().render_bullet_list_open({"type": "bullet_list_open"}, ctx)


@contrib_first
def render_html_tag_ul_close(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_pop()
    markdown_block().render_bullet_list_close({"type": "bullet_list_close"}, ctx)


@contrib_first
def render_html_tag_li_open(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_push(tag.name, style_spec)
    markdown_block().render_list_item_open({"type": "list_item_open"}, ctx)


@contrib_first
def render_html_tag_li_close(
    _, tag: Tag, ctx: Context, style_spec: Union[None, urwid.AttrSpec]
):
    ctx.tag_pop()
    markdown_block().render_list_item_close({"type": "list_item_close"}, ctx)
