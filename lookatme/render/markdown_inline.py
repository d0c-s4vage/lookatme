"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import contextlib
import re
import sys
import urwid


import lookatme.config as config
from lookatme.contrib import contrib_first
from lookatme.render.context import Context
import lookatme.render.pygments as pygments_render
from lookatme.utils import *
from lookatme.widgets.clickable_text import LinkIndicatorSpec
from lookatme.render.markdown_html import LookatmeHTMLParser


THIS_MOD = sys.modules[__name__]


def render(token, ctx: Context):
    """Render an inline token. These tokens come from "children" tokens of
    a block token.
    """
    with ctx.level_inc():
        fn = getattr(THIS_MOD, "render_{}".format(token["type"]), None)
        if fn is None:
            raise ValueError("Token type {!r} is not yet supported".format(token["type"]))
        return fn(token, ctx)


def render_all(tokens, ctx: Context):
    for token in tokens:
        ctx.log_debug("Rendering inline token: {!r}".format(token))
        render(token, ctx)


# -------------------------------------------------------------------------


def placeholder():
    """The starting point of the rendering. The final result will be this
    returned list with all inline markdown tokens translated into urwid objects
    """
    return []


def render_no_change(text, ctx: Context):
    """Render inline markdown text with no changes
    """
    ctx.inline_push((ctx.spec_text, text))


@contrib_first
def render_inline_html(token, ctx: Context):
    """Renders inline html as plaintext

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    LookatmeHTMLParser(ctx).feed(token["text"])


@contrib_first
def render_text(token, ctx: Context):
    """Renders plain text (does nothing)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    if ctx.is_literal:
        text = token["text"].replace("\r", "").replace("\n", " ")
    else:
        text = token["text"]
    ctx.inline_push((ctx.spec_text, text))


@contrib_first
def render_footnote_ref(token, ctx: Context):
    """Renders a footnote

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    raise NotImplementedError("render_footnote_ref is not implemented")


@contrib_first
def render_image(token, ctx: Context):
    """Renders an image as a link. This would be a cool extension to render
    referenced images as scaled-down ansii pixel blocks.

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    #raise NotImplementedError("render_image is not implemented")


@contrib_first
def render_link(token, ctx: Context):
    """Renders a link. This function does a few special things to make the
    clickable links happen. All text in lookatme is rendered using the
    :any:`ClickableText` class. The ``ClickableText`` class looks for
    ``urwid.AttrSpec`` instances that are actually ``LinkIndicatorSpec`` instances
    within the Text markup. If an AttrSpec is an instance of ``LinkIndicator``
    spec in the Text markup, ClickableText knows to handle clicks on that
    section of the text as a link.

    Example token:

    ..:code:

        {'type': 'link', 'link': 'https://google.com', 'children': [{'type': 'text', 'text': 'blah'}], 'title': None}
    """
    plain_spec = spec_from_style(config.STYLE["link"])
    link_spec = LinkIndicatorSpec(token["link"], token["link"], plain_spec)

    with ctx.use_spec(link_spec):
        render_all(token["children"], ctx)


@contrib_first
def render_strong(token, ctx: Context):
    """Renders double emphasis. Handles both ``**word**`` and ``__word__``
    """
    with ctx.use_spec(spec_from_style("underline")):
        render_all(token["children"], ctx)


@contrib_first
def render_emphasis(token, ctx: Context):
    """Renders double emphasis. Handles both ``*word*`` and ``_word_``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    with ctx.use_spec(spec_from_style("italics")):
        render_all(token["children"], ctx)


@contrib_first
def render_codespan(token, ctx: Context):
    """Renders inline code using the pygments renderer. This function also makes
    use of the coding style:

    .. code-block:: yaml

        style: monokai

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    spec, text = pygments_render.render_text(" " + token["text"] + " ", plain=True)[0]
    with ctx.use_spec(spec):
        ctx.inline_push((ctx.spec_text, text))


@contrib_first
def render_linebreak(token, ctx: Context):
    """Renders a line break
    """
    ctx.inline_push((ctx.spec_general, "\n"))


@contrib_first
def render_strikethrough(token, ctx: Context):
    """Renders strikethrough text (``~~text~~``)
    """
    with ctx.use_spec(spec_from_style("strikethrough")):
        render_all(token["children"], ctx)
