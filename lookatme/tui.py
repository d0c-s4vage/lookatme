"""
This module defines the text user interface (TUI) for lookatme
"""


import threading
import time
from collections import defaultdict
from queue import Queue, Empty
from typing import Tuple

import urwid

import lookatme.config
import lookatme.config as config
import lookatme.parser
from lookatme.slide import Slide
import lookatme.render.markdown_block as markdown_block
from lookatme.contrib import contrib_first, shutdown_contribs
from lookatme.render.context import Context
from lookatme.tutorial import tutor
from lookatme.utils import spec_from_style
from lookatme.widgets.clickable_text import ClickableText
import lookatme.widgets.codeblock as codeblock
from lookatme.widgets.scrollbar import Scrollbar
from lookatme.widgets.scroll_monitor import ScrollMonitor


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
        self.locks = defaultdict(threading.Lock)
        self.keep_running = threading.Event()
        self.queue = Queue()
        self.ctx = ctx
        self.cache = {}
        self._log = lookatme.config.get_log().getChild("RENDER")

    def flush_cache(self):
        """Clear everything out of the queue and the cache."""
        # clear all pending items
        with self.queue.mutex:
            self.queue.queue.clear()

        for _, lock in self.locks.items():
            lock.acquire()
        self.cache.clear()
        for _, lock in self.locks.items():
            lock.release()

    def queue_render(self, slide):
        """Queue up a slide to be rendered."""
        # just make sure it has been initialized
        self.locks[slide.number]
        if self.is_alive():
            self.queue.put(slide)
        else:
            self.render_slide(slide)

    def render_slide(self, slide):
        """Render a slide, blocking until the slide completes. If ``force`` is
        True, rerender the slide even if it is in the cache.
        """
        res = None
        with self.locks[slide.number]:
            if slide.number not in self.cache:
                self._cache_slide_render(slide)
            res = self.cache[slide.number]

        if isinstance(res, Exception):
            raise res
        return res

    def stop(self):
        self.keep_running.clear()
        # wait for all rendering to finish
        for _, lock in self.locks.items():
            lock.acquire()
            lock.release()

    def run(self):
        """Run the main render thread"""
        self.keep_running.set()
        while self.keep_running.is_set():
            try:
                to_render = self.queue.get(timeout=0.05)
            except Empty:
                continue
            with self.locks[to_render.number]:
                if to_render.number not in self.cache:
                    self._cache_slide_render(to_render)

    def _cache_slide_render(self, slide: Slide):
        try:
            self._log.debug("Rendering slide number {}".format(slide.number))
            res = self.do_render(slide, slide.number)
            self.cache[slide.number] = res
            self._log.debug("Done rendering slide number {}".format(slide.number))
        except Exception as e:
            self._log.error(
                f"Error occurred rendering slide {slide.number}", exc_info=True
            )

            try:
                curr_token = self.ctx.tokens.curr
            except:
                curr_token = None

            if curr_token:
                tmp = dict(**curr_token)
                if "unwound_token" in tmp:
                    del tmp["unwound_token"]

                self._log.error("Error occurred with token: {}".format(tmp))

                unwound_token = curr_token.get("unwound_token", {})
                if unwound_token:
                    self._log.error(
                        "Token resulted from unwinding {}".format(unwound_token)
                    )
                    unwound_context = self.ctx.source_get_token_lines(unwound_token, 10)
                    self._log.error(
                        "Unwound context:\n{}".format("\n".join(unwound_context))
                    )

                source_context = self.ctx.source_get_token_lines(curr_token, 10)
                self._log.error("Source context:\n{}".format("\n".join(source_context)))

            if self.is_alive():
                self.cache[slide.number] = e
            else:
                raise e

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

    @tutor(
        "general",
        "markdown supported features",
        r"""
        Lookatme supports most markdown features.

        |                         Supported | Not (yet) Supported |
        |----------------------------------:|---------------------|
        |                            Tables | Footnotes           |
        |                          Headings | *Images             |
        |                        Paragraphs |                     |
        |                      Block quotes |                     |
        |                     Ordered lists |                     |
        |                   Unordered lists |                     |
        | Code blocks & syntax highlighting |                     |
        |                 Inline code spans |                     |
        |                   Double emphasis |                     |
        |                   Single Emphasis |                     |
        |                     Strikethrough |                     |
        |                       Inline HTML |                     |
        |                             Links |                     |

        \*Images may be supported through extensions
        """,
        order=4,
    )
    def _render_tokens(self, tokens):
        tmp_listbox = urwid.ListBox([])

        self.ctx.clean_state_snapshot()

        with self.ctx.use_tokens(tokens):
            with self.ctx.use_container(tmp_listbox, is_new_block=True):
                markdown_block.render_all(self.ctx, and_unwind=True)

        self.ctx.clean_state_validate()

        return tmp_listbox.body


class MarkdownTui(urwid.Frame):
    def __init__(self, pres, start_idx=0, no_threads=False):
        """Create a new MarkdownTui"""
        self.slide_body = urwid.ListBox(
            urwid.SimpleFocusListWalker([urwid.Text("test")])
        )
        self.slide_body_scrollbar = Scrollbar(self.slide_body)
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
        self.scrolled_root_paddings = ScrollMonitor(
            self.root_paddings, self.slide_body_scrollbar
        )
        self.pres = pres

        self.init_ctx()

        self.root_widget = root_urwid_widget(self.root_margins)
        self.loop = urwid.MainLoop(
            self.ctx.wrap_widget(self.root_widget),
            screen=screen,
        )
        self.ctx.loop = self.loop
        self.no_threads = no_threads

        self._slide_focus_cache = {}

        # used to track slides that are being rendered
        self.slide_renderer = SlideRenderer(self.ctx.clone())
        if not no_threads:
            self.slide_renderer.start()

        self.prep_pres(self.pres, start_idx)

        urwid.Frame.__init__(
            self,
            self.scrolled_root_paddings,
            self.top_spacing_box,
            self.bottom_spacing_box,
        )

    def set_slide_idx(self, slide_idx: int) -> Slide:
        self.curr_slide = self.pres.slides[slide_idx]
        self.update()
        return self.curr_slide

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

    @tutor(
        "general",
        "title",
        r"""
        Notice the **title** up top *↑*  You can set it through

        ## 1. Smart Slide Splitting

        The first, lowest-level heading becomes the title, the next highest level
        splits the slides

        ```md
        # My title

        ## Slide 1

        contents
        ```

        ## 2. Metadata

        Set the title explicitly through YAML metadata at the start of the slide:

        ```md
        ---
        title: My title
        ---

        # Slide 1

        Slide contents
        ```

        > **NOTE** Metadata and styling will be covered later in this tutorial
        >
        > **NOTE** `h | k | delete | backspace | left arrow` reverse the slides
        """,
        order=1,
    )
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
                markdown_block.render_all(self.ctx, and_unwind=True)
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

        self._restore_slide_scroll_state()

        scroll_style = config.get_style()["scrollbar"]

        self.slide_body_scrollbar.gutter_spec = self.ctx.spec_text_with(
            spec_from_style(scroll_style["gutter"])
        )
        self.slide_body_scrollbar.gutter_fill_char = scroll_style["gutter"]["fill"]

        self.slide_body_scrollbar.slider_top_chars = scroll_style["slider"]["top_chars"]
        self.slide_body_scrollbar.slider_bottom_chars = scroll_style["slider"][
            "bottom_chars"
        ]
        self.slide_body_scrollbar.slider_spec = self.ctx.spec_text_with(
            spec_from_style(scroll_style["slider"])
        )
        self.slide_body_scrollbar.slider_fill_char = scroll_style["slider"]["fill"]

    def update_slide_settings(self):
        """Update the slide margins and paddings"""
        style = config.get_style()

        # reset the base spec from the slides settings
        self.ctx.spec_pop()
        self.ctx.spec_push(spec_from_style(style["slides"]))
        # re-wrap the root widget with the new styles
        self.loop.widget = self.ctx.wrap_widget(self.root_widget)

        margin = style["margin"]
        padding = style["padding"]

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

    def init_ctx(self):
        self.ctx = Context(None)
        self.ctx.source_push(self.pres.no_meta_source)
        self.ctx.spec_push(spec_from_style(config.get_style()["slides"]))

    def reload(self):
        """Reload the input, keeping the current slide in focus"""
        self._cache_slide_scroll_state()

        self.init_ctx()
        self.slide_renderer.ctx = self.ctx

        codeblock.clear_cache()

        curr_slide_idx = self.curr_slide.number
        self.slide_renderer.flush_cache()
        self.pres.reload()
        self.prep_pres(self.pres, curr_slide_idx)
        self.update()

    @tutor(
        "general",
        "Navigation and Keybindings",
        r"""
        Slides are navigated using vim direction keys, arrow keys, and page up/page down:

        |                key(s) | action                  |
        |----------------------:|-------------------------|
        | `l` `j` `right arrow` | Next slide              |
        |  `h` `k` `left arrow` | Previous slide          |
        |      up / down arrows | Scroll by line          |
        |   page up / page down | Scroll by pages         |
        |                   `r` | Reload                  |
        """,
        order=0.1,
    )
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

        self._cache_slide_scroll_state()
        self.curr_slide = self.pres.slides[new_slide_num]
        self.update()

    def _cache_slide_scroll_state(self):
        self._slide_focus_cache[self.curr_slide.number] = (
            self.slide_body.offset_rows,
            self.slide_body.focus_position,
        )

    def _restore_slide_scroll_state(self):
        offset_rows, focus_pos = self._slide_focus_cache.setdefault(
            self.curr_slide.number, (0, 0)
        )
        self.slide_body.set_focus(focus_pos)
        self.slide_body.offset_rows = offset_rows

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

    def render_without_scrollbar(self, width: int) -> Tuple:
        """Return a tuple of three canvases: (header, body, footer)"""
        padding_amt = self.root_paddings.left + self.root_paddings.right
        content_width = width - padding_amt

        content_size = 0
        for widget in self.slide_body.body:
            _, rows = widget.pack((content_width,), True)
            content_size += rows

        header_canvas = self.get_header().render((width,), False)
        body_canvas = self.get_body().render((width, content_size), True)
        footer_canvas = self.get_footer().render((width,), False)

        return header_canvas, body_canvas, footer_canvas


def create_tui(pres, start_slide=0, no_threads=False):
    """Run the provided presentation

    :param int start_slide: 0-based slide index
    """
    tui = MarkdownTui(pres, start_slide, no_threads=no_threads)
    return tui
