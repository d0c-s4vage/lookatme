"""
This module tests contrib-specific functionality
"""

import urwid
from six.moves import reload_module, StringIO


import lookatme.pres
import lookatme.contrib
import lookatme.contrib.terminal
import lookatme.contrib.file_loader
import lookatme.tui
import lookatme.render.markdown_block
import lookatme.render.markdown_inline


def setup_contrib(fake_mod):
    lookatme.contrib.CONTRIB_MODULES = [
        lookatme.contrib.terminal,
        lookatme.contrib.file_loader,
        fake_mod
    ]
    reload_module(lookatme.render.markdown_block)
    reload_module(lookatme.render.markdown_inline)
    reload_module(lookatme.tui)


def test_overridable_root(mocker):
    """Ensure that the root urwid component is overridable
    """
    lookatme.config.LOG = mocker.Mock()

    class Wrapper(urwid.WidgetWrap): pass

    class FakeMod:
        @staticmethod
        def root_urwid_widget(to_wrap):
            return Wrapper(to_wrap)
    
    setup_contrib(FakeMod)
    input_stream = StringIO("test")
    pres = lookatme.pres.Presentation(input_stream, "dark")
    tui = lookatme.tui.MarkdownTui(pres)

    assert isinstance(tui.loop.widget, Wrapper)
