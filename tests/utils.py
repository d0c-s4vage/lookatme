"""
Defines utilities for testing lookatme
"""


import pytest
import urwid


from lookatme.parser import Parser
import lookatme.tui


def assert_render(correct_render, rendered, full_strip=False):
    for idx, row in enumerate(rendered):
        if full_strip:
            stripped = row_text(row).strip()
        else:
            stripped = row_text(row).rstrip()
        if idx >= len(correct_render):
            assert stripped == b""
        else:
            assert correct_render[idx] == stripped


def render_markdown(markdown, height=50, width=200, single_slide=False):
    """Returns the rendered canvas contents of the markdown
    """
    loop = urwid.MainLoop(urwid.ListBox([]))
    renderer = lookatme.tui.SlideRenderer(loop)
    renderer.start()

    parser = Parser(single_slide=single_slide)
    _, slides = parser.parse_slides({"title": ""}, markdown)

    renderer.stop()
    contents = renderer.render_slide(slides[0], force=True)
    renderer.join()

    container = urwid.ListBox([urwid.Text("testing")])
    container.body = contents
    return list(container.render((width,height)).content())


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
