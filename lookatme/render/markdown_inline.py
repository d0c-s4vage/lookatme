"""
Defines render functions that work with mistune's markdown inline lexer render
interface
"""


import contextlib
import urwid


import lookatme.config as config
from lookatme.utils import *
import lookatme.render.pygments as pygments_render


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


inline_html = render_no_change
text = render_no_change
escape = render_no_change


def autolink(link_uri, is_email=False):
    return link(link_uri, None, link_uri)


def inline_html(html):
    return render_no_change(html)


def footnote_ref(key, index):
    __import__('pdb').set_trace()
    return render_no_change(key)


def image(link_uri, title, text):
    return link(link_uri, title, text)


def link(link_uri, title, text):
    return [styled_text(text, config.STYLE["link"])]


@expanded_styles
def double_emphasis(text, old_styles):
    return [styled_text(text, "underline", old_styles)]


@expanded_styles
def emphasis(text, old_styles):
    return [styled_text(text, "italics", old_styles)]


@expanded_styles
def underline(text, old_styles):
    return [styled_text(text, "underline", old_styles)]


@expanded_styles
def codespan(text, old_styles):
    res = pygments_render.render_text(" " + text + " ", plain=True)
    return res


def linebreak():
    return ["\n"]


@expanded_styles
def strikethrough(text, old_styles):
    return [styled_text(text, "strikethrough", old_styles)]
