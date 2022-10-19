"""
This module defines the text user interface (TUI) for lookatme
"""


import threading
import time
from collections import defaultdict
from queue import Queue, Empty

import urwid

import lookatme.config
import lookatme.config as config
import lookatme.parser
import lookatme.render.markdown_block as markdown_block
from lookatme.contrib import contrib_first, shutdown_contribs
from lookatme.render.context import Context
from lookatme.utils import spec_from_style
from lookatme.widgets.clickable_text import ClickableText


def text(style, data, align="left"):
    if isinstance(style, dict):
        style = spec_from_style(style)
    return urwid.Text((style, data), align=align)


@contrib_first
def root_urwid_widget(to_wrap):
    """This function is overridable by contrib extensions that need to specify
    the root urwid widget.

    The return value *must* return either the ``to_wrap`` widget itself, or
    another widget that wraps the provided ``to_wrap`` widget.
    """
    return to_wrap


class SlideRenderer(threading.Thread):
    daemon = True

    def __init__(self, ctx: Context):
        threading.Thread.__init__(self)
        self.events = defaultdict(threading.Event)
        self.keep_running = threading.Event()
        self.queue = Queue()
        self.ctx = ctx
        self.cache = {}
        self._log = lookatme.config.get_log().getChild("RENDER")

    def flush_cache(self):
        """Clea everything out of the queue and the cache."""
        # clear all pending items
        with self.queue.mutex:
            self.queue.queue.clear()
        self.cache.clear()

    def queue_render(self, slide):
        """Queue up a slide to be rendered."""
        self.events[slide.number].clear()
        self.queue.put(slide)

    def render_slide(self, slide, force=False):
        """Render a slide, blocking until the slide completes. If ``force`` is
        True, rerender the slide even if it is in the cache.
        """
        if force or slide.number not in self.cache:
            self.events[slide.number].clear()
            self.queue.put(slide)
            self.events[slide.number].wait()

        res = self.cache[slide.number]
        if isinstance(res, Exception):
            raise res
        return res

    def stop(self):
        self.keep_running.clear()

    def run(self):
        """Run the main render thread"""
        self.keep_running.set()
        while self.keep_running.is_set():
            try:
                to_render = self.queue.get(timeout=0.05)
            except Empty:
                continue

            slide_num = to_render.number

            try:
                res = self.do_render(to_render, slide_num)
                self.cache[slide_num] = res
            except Exception as e:
                self.cache[slide_num] = e
            finally:
                self.events[slide_num].set()

    def do_render(self, to_render, slide_num):
        """Perform the actual rendering of a slide. This is done by:

          * parsing the slide into tokens (should have occurred already)
          * iterating through each parsed markdown token
          * calling the appropriately-named render function for the ``token["type"]``
            in :py:mod:`lookatme.render.markdown_block`

        Each render function must have the signature:

        .. code-block:: python

            def render_XXX(token, body, stack, loop):
                pass

        The arguments to the render function are described below:

          * ``token`` - the lexed markdown token - a dictionary
          * ``body`` - the current ``urwid.Pile()`` that return values will be
            added to (same as ``stack[-1]``)
          * ``stack`` - The stack of ``urwid.Pile()`` used during rendering.
            E.g., when rendering nested lists, each nested list will push a new
            ``urwid.Pile()`` to the stack, each wrapped with its own additional
            indentation.
          * ``loop`` - the ``urwid.MainLoop`` instance being used by lookatme.
            This won't usually be used, but is available if needed.

        Main render functions (those defined in markdown_block.py) may have
        three types of return values:

          * ``None`` - nothing is added to ``stack[-1]``. Perhaps the render
            function only needed to add additional indentation by pushing a new
            ``urwid.Pile()`` to the stack.
          * ``list(urwid.Widget)`` - A list of widgets to render. These will
            automatically be added to the Pile at ``stack[-1]``
          * ``urwid.Widget`` - A single widget to render. Will be added to
            ``stack[-1]`` automatically.
        """
        self._log.debug(f"Rendering slide {slide_num}")
        start = time.time()

        # initial processing loop - results are discarded, but render functions
        # may add extra metadata to the token itself. For example, list rendering
        # uses this to determine the max indent size for each level.
        tokens = to_render.tokens
        self._log.debug("")
        self._log.debug("PRE-Render====================================")
        self._log.debug("")
        self._render_tokens(tokens)
        self._log.debug("")
        self._log.debug("FINAL-Render====================================")
        self._log.debug("")
        res = self._render_tokens(tokens)

        total = time.time() - start
        self._log.debug(f"Rendered slide {slide_num} in {total}")

        return res

    def _render_tokens(self, tokens):
        tmp_listbox = urwid.ListBox([])
        with self.ctx.use_tokens(tokens):
            with self.ctx.use_container(tmp_listbox, is_new_block=True):
                markdown_block.render_all(self.ctx)

        return tmp_listbox.body


class MarkdownTui(urwid.Frame):
    def __init__(self, pres, start_idx=0):
        """Create a new MarkdownTui"""
        # self.slide_body = urwid.Pile(urwid.SimpleListWalker([urwid.Text("test")]))
        self.slide_body = urwid.ListBox(
            urwid.SimpleFocusListWalker([urwid.Text("test")])
        )
        self.slide_title = ClickableText([""], align="center")
        self.top_spacing = urwid.Filler(self.slide_title, top=0, bottom=0)
        self.top_spacing_box = urwid.BoxAdapter(self.top_spacing, 1)

        self.creation = text("", "")
        self.slide_num = text("", " test ", "right")
        self.slide_footer = urwid.Columns([self.creation, self.slide_num])
        self.bottom_spacing = urwid.Filler(self.slide_footer, top=0, bottom=0)
        self.bottom_spacing_box = urwid.BoxAdapter(self.bottom_spacing, 1)

        self._log = lookatme.config.get_log()

        urwid.set_encoding("utf8")
        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)

        self.root_margins = urwid.Padding(self, left=2, right=2)
        self.root_paddings = urwid.Padding(self.slide_body, left=10, right=10)

        self.ctx = Context(None)
        self.ctx.spec_push(spec_from_style(config.get_style()["slides"]))

        self.root_widget = root_urwid_widget(self.root_margins)
        self.loop = urwid.MainLoop(
            self.ctx.wrap_widget(self.root_widget),
            screen=screen,
        )
        self.ctx.loop = self.loop

        # used to track slides that are being rendered
        self.slide_renderer = SlideRenderer(self.ctx)
        self.slide_renderer.start()

        self.pres = pres
        self.prep_pres(self.pres, start_idx)

        urwid.Frame.__init__(
            self,
            self.root_paddings,
            self.top_spacing_box,
            self.bottom_spacing_box,
        )

    def prep_pres(self, pres, start_idx=0):
        """Prepare the presentation for displaying/use"""
        self.curr_slide = self.pres.slides[start_idx]
        self.update()

        # now queue up the rest of the slides while we're at it so they'll be
        # ready when we need them
        for slide in filter(lambda x: x.number != start_idx, self.pres.slides):
            self.slide_renderer.queue_render(slide)

    def update_slide_num(self):
        """Update the slide number"""
        slide_text = "slide {} / {}".format(
            self.curr_slide.number + 1,
            len(self.pres.slides),
        )
        spec = spec_from_style(config.get_style()["slide_number"])
        spec = self.ctx.spec_text_with(spec)
        self.slide_num.set_text([(spec, slide_text)])

    def update_title(self):
        """Update the title"""
        title = self.pres.meta.get("title", "")
        if isinstance(title, str):
            tokens = lookatme.parser.md_to_tokens(title)
        else:
            tokens = title

        expected_types = ["paragraph_open", "inline", "paragraph_close"]
        if tokens and [x["type"] for x in tokens] != expected_types:
            raise ValueError(
                "Titles must only be inline markdown, was {}".format(
                    [x["type"] for x in tokens]
                )
            )

        title = [] if not tokens else [tokens[1]]  # the inline token
        spec = spec_from_style(config.get_style()["title"])

        if not title:
            return

        with self.ctx.use_tokens(title):
            with self.ctx.use_spec(spec):
                markdown_block.render_all(self.ctx)
        self.slide_title.set_text(self.ctx.inline_markup_consumed)

    def update_creation(self):
        """Update the author and date"""
        author = self.pres.meta.get("author", "")
        author_spec = spec_from_style(config.get_style()["author"])
        author_spec = self.ctx.spec_text_with(author_spec)

        date = self.pres.meta.get("date", "")
        date_spec = spec_from_style(config.get_style()["date"])
        date_spec = self.ctx.spec_text_with(date_spec)

        markups = []
        if author not in ("", None):
            markups.append((author_spec, author))
        if date not in ("", None):
            if len(markups) > 0:
                markups.append(" ")
            markups.append((date_spec, date))

        self.creation.set_text(markups)

    def update_body(self):
        """Render the provided slide body"""
        rendered = self.slide_renderer.render_slide(self.curr_slide)
        self.slide_body.body = rendered

    def update_slide_settings(self):
        """Update the slide margins and paddings"""
        # reset the base spec from the slides settings
        self.ctx.spec_pop()
        self.ctx.spec_push(spec_from_style(config.get_style()["slides"]))
        # re-wrap the root widget with the new styles
        self.loop.widget = self.ctx.wrap_widget(self.root_widget)

        margin = config.get_style()["margin"]
        padding = config.get_style()["padding"]

        self.root_margins.left = margin["left"]
        self.root_margins.right = margin["right"]

        self.root_paddings.left = padding["left"]
        self.root_paddings.right = padding["right"]

        self.top_spacing.top = margin["top"]
        self.top_spacing.bottom = padding["top"]
        self.top_spacing_box.height = margin["top"] + 1 + padding["top"]

        self.bottom_spacing.top = padding["bottom"]
        self.bottom_spacing.bottom = margin["bottom"]
        self.bottom_spacing_box.height = margin["bottom"] + 1 + padding["bottom"]

    def update(self):
        """ """
        self.update_slide_settings()
        self.update_slide_num()
        self.update_title()
        self.update_creation()
        self.update_body()

    def reload(self):
        """Reload the input, keeping the current slide in focus"""
        curr_slide_idx = self.curr_slide.number
        self.slide_renderer.flush_cache()
        self.pres.reload()
        self.prep_pres(self.pres, curr_slide_idx)
        self.update()

    def keypress(self, size, key):
        """Handle keypress events"""
        self._log.debug(f"KEY: {key}")
        key = self._get_key(size, key)
        if key is None:
            return

        slide_direction = 0
        if key in ["left", "backspace", "delete", "h", "k"]:
            slide_direction = -1
        elif key in ["right", " ", "j", "l"]:
            slide_direction = 1
        elif key in ["q", "Q"]:
            shutdown_contribs()
            raise urwid.ExitMainLoop()
        elif key == "r":
            self.reload()

        if slide_direction == 0:
            return

        new_slide_num = self.curr_slide.number + slide_direction
        if new_slide_num < 0:
            new_slide_num = 0
        elif new_slide_num >= len(self.pres.slides):
            new_slide_num = len(self.pres.slides) - 1

        if new_slide_num == self.curr_slide.number:
            return

        self.curr_slide = self.pres.slides[new_slide_num]
        self.update()

    def _get_key(self, size, key):
        """Resolve the key that was pressed."""
        try:
            key = urwid.Frame.keypress(self, size, key)
            if key is None:
                return
        except Exception:
            pass
        return key

    def run(self):
        self.loop.run()


def create_tui(pres, start_slide=0):
    """Run the provided presentation

    :param int start_slide: 0-based slide index
    """
    tui = MarkdownTui(pres, start_slide)
    return tui
