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
from lookatme.widgets.clickable_text import ClickableText
from lookatme.render.context import Context
import lookatme.render.pygments as pygments_render
from lookatme.utils import *
from lookatme.widgets.clickable_text import LinkIndicatorSpec
from lookatme.render.markdown_html import LookatmeHTMLParser


THIS_MOD = sys.modules[__name__]


def expanded_styles(fn):
    @contextlib.wraps(fn)
    def inner(text):
        styles = dict(fg="", bg="")
        if isinstance(text, str):
            return fn(text, styles)
        elif isinstance(text, list) and isinstance(text[0], str):
            return fn(text[0], styles)
        elif isinstance(text, list) and isinstance(text[0], tuple):
            attr_spec = text[0][0]
            styles = dict(fg=attr_spec.foreground, bg=attr_spec.background)
            text = text[0][1]
            return fn(text, styles)
        else:
            return fn(text, styles)
    return inner


def render(token, ctx: Context):
    """Render an inline token. These tokens come from "children" tokens of
    a block token.
    """
    fn = getattr(THIS_MOD, "render_{}".format(token["type"]), None)
    if fn is None:
        raise ValueError("Token type {!r} is not yet supported".format(token["type"]))
    return fn(token, ctx)


def render_inline_children(children, ctx: Context):
    res = []
    prev = None
    for child_token in children:
        curr_res = render(child_token, ctx)
        res += curr_res

    return res

def render_tokens_full(children, ctx: Context):
    """Render all inline tokens and fully resolve them to widgets (not just
    urwid text markup).

    .. note: plugins may override some of these inlinen rendering functions to
        return a full widget instead of markup text, especially with the image
        related plugins.
    """
    res = []
    curr_text_markup = []
    for item in render_inline_children(children, ctx):
        if isinstance(item, urwid.Widget):
            if len(curr_text_markup) > 0:
                res.append(ClickableText(curr_text_markup))
                curr_text_markup = []
            res.append(item)
        if isinstance(item, str) or (isinstance(item, (tuple|list)) and len(item) == 2):
            curr_text_markup.append(item)

    if len(curr_text_markup) > 0:
        res.append(ClickableText(curr_text_markup))

    return res

# -------------------------------------------------------------------------


def placeholder():
    """The starting point of the rendering. The final result will be this
    returned list with all inline markdown tokens translated into urwid objects
    """
    return []


def render_no_change(text, ctx: Context):
    """Render inline markdown text with no changes
    """
    return [(ctx.spec, text)]


OPEN_TAG_MATCHER = re.compile(r"""
    ^                                      # match the start of the string
    <(?P<tag>[a-z]+)\s*                    # <tag followed by one or more spaces
        (\s+style=['"]                     # style attribute with ' or " quotes
            color:\s*(?P<color>[#a-z0-9]+) # only the color attribute
        ['"]                               # end with either ' or " quotes
    )?>                                    # close the opening tag, opt attrs
    $                                      # end of the string
""", re.VERBOSE | re.MULTILINE | re.IGNORECASE)
CLOSE_TAG_MATCHER = re.compile(r'</(?P<tag>[a-z]+)>')

SPAN_MATCHER2 = re.compile(
    r'^<span\s+style=[\'"]\s*color:\s*(?P<color>[#a-z0-9A-Z]+)[\'"]>(?P<content>.*)</span>$',
    re.VERBOSE | re.MULTILINE | re.IGNORECASE
)


@contrib_first
def render_inline_html(token, ctx: Context):
    """Renders inline html as plaintext

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    parser = LookatmeHTMLParser(ctx, THIS_MOD)
    parser.feed(token["text"])
    return []


@contrib_first
def render_text(token, ctx: Context):
    """Renders plain text (does nothing)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    text = token["text"]
    if not ctx.is_literal:
        text = token["text"].replace("\r", "").replace("\n", " ")
    return [(ctx.spec, text)]


@contrib_first
def render_escape(token, ctx: Context):
    """Renders escapes

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text, ctx)


@contrib_first
def render_autolink(token, ctx: Context):
    """Renders a URI as a link

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_link(token, ctx)


@contrib_first
def render_footnote_ref(token, ctx: Context):
    """Renders a footnote

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(key, ctx)


@contrib_first
def render_image(token, ctx: Context):
    """Renders an image as a link. This would be a cool extension to render
    referenced images as scaled-down ansii pixel blocks.

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_link(token, ctx)

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

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    plain_spec = spec_from_style(config.STYLE["link"])
    link_spec = LinkIndicatorSpec(token["link"], token["link"], plain_spec)

    with ctx.use_spec(link_spec):
        return render_inline_children(token["children"], ctx)


@contrib_first
def render_strong(token, ctx: Context):
    """Renders double emphasis. Handles both ``**word**`` and ``__word__``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    with ctx.use_spec(spec_from_style("underline")):
        return render_inline_children(token["children"], ctx)


@contrib_first
def render_emphasis(token, ctx: Context):
    """Renders double emphasis. Handles both ``*word*`` and ``_word_``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    with ctx.use_spec(spec_from_style("italics")):
        return render_inline_children(token["children"], ctx)


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
        return [(ctx.spec, text)]


@contrib_first
def render_linebreak(token, ctx: Context):
    """Renders a line break

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return ["\n"]


@contrib_first
def render_strikethrough(token, ctx: Context):
    """Renders strikethrough text (``~~text~~``)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    with ctx.use_spec(spec_from_style("strikethrough")):
        return render_inline_children(token["children"], ctx)
