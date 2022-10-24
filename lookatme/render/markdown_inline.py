"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import functools

import lookatme.config as config
import lookatme.render.pygments as pygments_render
import lookatme.utils as utils
from lookatme.contrib import contrib_first
from lookatme.tutorial import tutor
from lookatme.widgets.clickable_text import LinkIndicatorSpec

options = {}


def expanded_styles(fn):
    @functools.wraps(fn)
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
def inline_html(text):
    """Renders inline html as plaintext

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text)


@contrib_first
def text(text):
    """Renders plain text (does nothing)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text)


@contrib_first
def escape(text):
    """Renders escapes

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(text)


@contrib_first
def autolink(link_uri, is_email=False):
    """Renders a URI as a link

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return link(link_uri, None, link_uri)


@contrib_first
def footnote_ref(key, index):
    """Renders a footnote

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return render_no_change(key)


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
    """
)
@contrib_first
def image(link_uri, title, text):
    """Renders an image as a link. This would be a cool extension to render
    referenced images as scaled-down ansii pixel blocks.

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return link(link_uri, title, text)


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
    """
)
@contrib_first
def link(link_uri, title, link_text):
    """Renders a link. This function does a few special things to make the
    clickable links happen. All text in lookatme is rendered using the
    :any:`ClickableText` class. The ``ClickableText`` class looks for
    ``urwid.AttrSpec`` instances that are actually ``LinkIndicatorSpec`` instances
    within the Text markup. If an AttrSpec is an instance of ``LinkIndicator``
    spec in the Text markup, ClickableText knows to handle clicks on that
    section of the text as a link.

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    raw_link_text = []
    for x in link_text:
        if isinstance(x, tuple):
            raw_link_text.append(x[1])
        else:
            raw_link_text.append(x)
    raw_link_text = "".join(raw_link_text)

    spec, text = utils.styled_text(
        link_text, utils.spec_from_style(config.get_style()["link"]))
    spec = LinkIndicatorSpec(raw_link_text, link_uri, spec)
    return [(spec, text)]


@tutor(
    "markdown",
    "emphasis",
    r"""
    <TUTOR:EXAMPLE>
    The donut jumped *under* the crane.
    </TUTOR:EXAMPLE>
    """
)
@expanded_styles
@contrib_first
def emphasis(text, old_styles):
    """Renders double emphasis. Handles both ``*word*`` and ``_word_``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return [utils.styled_text(text, "italics", old_styles)]


@tutor(
    "markdown",
    "double emphasis",
    r"""
    <TUTOR:EXAMPLE>
    They jumped **over** the wagon
    </TUTOR:EXAMPLE>
    """
)
@expanded_styles
@contrib_first
def double_emphasis(text, old_styles):
    """Renders double emphasis. Handles both ``**word**`` and ``__word__``

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return [utils.styled_text(text, "underline", old_styles)]


@tutor(
    "markdown",
    "inline code",
    r"""
    <TUTOR:EXAMPLE>
    The `OddOne` class accepts `Table` instances, converts them to raw pointers,
    forces garbage collection to run.
    </TUTOR:EXAMPLE>
    """
)
@expanded_styles
@contrib_first
def codespan(text, old_styles):
    """Renders inline code using the pygments renderer. This function also makes
    use of the coding style:

    .. code-block:: yaml

        style: monokai

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    res = pygments_render.render_text(" " + text + " ", plain=True)
    return res


@contrib_first
def linebreak():
    """Renders a line break

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return ["\n"]


@tutor(
    "markdown",
    "strikethrough",
    r"""
    <TUTOR:EXAMPLE>
    I lost my ~~mind~~ keyboard and couldn't type anymore.
    </TUTOR:EXAMPLE>
    """
)
@expanded_styles
@contrib_first
def strikethrough(text, old_styles):
    """Renders strikethrough text (``~~text~~``)

    :returns: list of `urwid Text markup <http://urwid.org/manual/displayattributes.html#text-markup>`_
        tuples.
    """
    return [utils.styled_text(text, "strikethrough", old_styles)]
