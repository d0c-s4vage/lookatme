"""
Defines utilities for testing lookatme
"""


import pytest
import urwid


from lookatme.parser import Parser
import lookatme.tui


def render_markdown(markdown, height=50):
    """Returns the rendered canvas contents of the markdown
    """
    loop = urwid.MainLoop(urwid.Pile([]))
    renderer = lookatme.tui.SlideRenderer(loop)
    renderer.start()

    parser = Parser()
    _, slides = parser.parse_slides({"title": ""}, markdown)

    renderer.stop()
    pile_contents = renderer.render_slide(slides[0], force=True)
    renderer.join()

    pile = urwid.Pile([urwid.Text("testing")])
    pile.contents = pile_contents
    return list(pile.render((height,)).content())


def spec_and_text(item):
    """``item`` should be an item from a rendered widget, a tuple of the form

    .. code-block:: python

        (spec, ?, text)
    """
    return item[0], item[2]


def row_text(rendered_row):
    """Return all text joined together from the rendered row
    """
    return b"".join(x[-1] for x in rendered_row)
