"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import contextlib
import sys
import urwid


import lookatme.config as config
from lookatme.contrib import contrib_first
from lookatme.widgets.clickable_text import ClickableText
import lookatme.render.pygments as pygments_render
from lookatme.utils import *
from lookatme.widgets.clickable_text import LinkIndicatorSpec


options = {}


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


THIS_MOD = sys.modules[__name__]
def render(token, body, stack, loop, spec_stack=None):
    """Render an inline token. These tokens come from "children" tokens of
    a block token.
    """
    if spec_stack is None:
        spec_stack = []

    fn = getattr(THIS_MOD, "render_{}".format(token["type"]), None)
    if fn is None:
        raise ValueError("Token type {!r} is not yet supported".format(token["type"]))
    return fn(token, body, stack, loop, spec_stack)


def render_inline_children(children, body, stack, loop, spec_stack=None):
    if spec_stack is None:
        spec_stack = []

    res = []
    prev = None
    for child_token in children:
        curr_res = render(child_token, body, stack, loop, spec_stack)
        res += curr_res

    return res

# -------------------------------------------------------------------------


def placeholder():
    """The starting point of the rendering. The final result will be this
    returned list with all inline markdown tokens translated into urwid objects
    """
    return []


def render_no_change(text):
    """Render inline markdown text with no changes
    """
    return [text]


@contrib_first
def render_inline_html(text):
    """Renders inline html as plaintext

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text)


@contrib_first
def render_text(token, body, stack, loop, spec_stack):
    """Renders plain text (does nothing)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    final_spec = spec_from_stack(spec_stack)
    return [(final_spec, token["text"])]


@contrib_first
def render_escape(token, body, stack, loop, spec_stack):
    """Renders escapes

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text)


@contrib_first
def render_autolink(token, body, stack, loop, spec_stack):
    """Renders a URI as a link

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return link(link_uri, None, link_uri)


@contrib_first
def render_footnote_ref(token, body, stack, loop, spec_stack):
    """Renders a footnote

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(key)


@contrib_first
def render_image(token, body, stack, loop, spec_stack):
    """Renders an image as a link. This would be a cool extension to render
    referenced images as scaled-down ansii pixel blocks.

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return link(link_uri, title, text)

LINK_ID = 0

@contrib_first
def render_link(token, body, stack, loop, spec_stack):
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
    global LINK_ID

    plain_spec = spec_from_style(config.STYLE["link"])
    link_spec = LinkIndicatorSpec(token["link"], token["link"], LINK_ID, plain_spec)
    LINK_ID += 1

    return render_inline_children(token["children"], body, stack, loop, spec_stack + [link_spec])


@contrib_first
def render_double_emphasis(token, body, stack, loop, spec_stack):
    """Renders double emphasis. Handles both ``**word**`` and ``__word__``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return [styled_text(text, "underline", old_styles)]


@contrib_first
def render_emphasis(token, body, stack, loop, spec_stack):
    """Renders double emphasis. Handles both ``*word*`` and ``_word_``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    this_spec = spec_from_style("italics")
    return render_inline_children(token["children"], body, stack, loop, spec_stack + [this_spec])


@contrib_first
def render_codespan(token, body, stack, loop, spec_stack):
    """Renders inline code using the pygments renderer. This function also makes
    use of the coding style:

    .. code-block:: yaml

        style: monokai

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    spec, text = pygments_render.render_text(token["text"], plain=True)[0]
    final_spec = spec_from_stack(spec_stack + [spec])
    return [(final_spec, text)]


@contrib_first
def render_linebreak(token, body, stack, loop, spec_stack):
    """Renders a line break

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return ["\n"]


@contrib_first
def render_strikethrough(token, body, stack, loop, spec_stack):
    """Renders strikethrough text (``~~text~~``)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return [styled_text(text, "strikethrough", old_styles)]
