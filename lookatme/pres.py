"""
Defines Presentation specific objects
"""


from collections import OrderedDict
import inspect
import os
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple


import urwid


import lookatme.ascii_art
import lookatme.config
import lookatme.contrib
import lookatme.prompt
import lookatme.themes
import lookatme.tui
from lookatme.parser import Parser
from lookatme.tutorial import tutor
import lookatme.render.html as html


DEFAULT_HTML_OPTIONS = {
    "width": 100,
    "title_delim": ":",
}


@tutor(
    "general",
    "intro",
    r"""
    `lookatme` is a terminal-based markdown presentation tool.

    That means that you can:

     | Write                 | Render          | Use                            |
     |-----------------------|-----------------|--------------------------------|
     | basic markdown slides | in the terminal | anywhere with markdown support |

    Press `l`, `j`, or `right arrow` to go to the next slide, or `q` to quit.
    """,
    order=0,
)
class Presentation(object):
    """Defines a presentation"""

    def __init__(
        self,
        input_stream,
        theme: str = "dark",
        live_reload=False,
        single_slide=False,
        preload_extensions=None,
        safe=False,
        no_ext_warn=False,
        ignore_ext_failure=False,
        no_threads=False,
    ):
        """Creates a new Presentation

        :param stream input_stream: An input stream from which to read the
            slide data
        """
        self.preload_extensions = preload_extensions or []
        self.input_filename = None
        if hasattr(input_stream, "name"):
            lookatme.config.SLIDE_SOURCE_DIR = os.path.dirname(input_stream.name)
            self.input_filename = input_stream.name

        self.live_reload = live_reload
        self.tui = None
        self.single_slide = single_slide
        self.safe = safe
        self.no_ext_warn = no_ext_warn
        self.ignore_ext_failure = ignore_ext_failure
        self.initial_load_complete = False
        self.no_threads = no_threads
        self.cli_theme = theme

        if self.live_reload:
            self.reload_thread = threading.Thread(target=self.reload_watcher)
            self.reload_thread.daemon = True
            self.reload_thread.start()

        self.reload(data=input_stream.read())
        self.initial_load_complete = True

    def reload_watcher(self):
        """Watch for changes to the input filename, automatically reloading
        when the modified time has changed.
        """
        if self.input_filename is None:
            return

        last_mod_time = os.path.getmtime(self.input_filename)
        while True:
            try:
                curr_mod_time = os.path.getmtime(self.input_filename)
                if curr_mod_time != last_mod_time:
                    self.get_tui().reload()
                    self.get_tui().loop.draw_screen()
                    last_mod_time = curr_mod_time
            except Exception:
                pass
            finally:
                time.sleep(0.25)

    def reload(self, data=None):
        """Reload this presentation

        :param str data: The data to render for this slide deck (optional)
        """
        if data is None:
            with open(str(self.input_filename), "r") as f:
                data = f.read()

        parser = Parser(single_slide=self.single_slide)
        self.meta, self.slides, self.no_meta_source = parser.parse(data)

        # only load extensions once! Live editing does not support
        # auto-extension reloading
        if not self.initial_load_complete:
            safe_exts = set(self.preload_extensions)
            new_exts = set()
            # only load if running with safe=False
            if not self.safe:
                source_exts = set(self.meta.get("extensions", []))
                new_exts = source_exts - safe_exts
                self.warn_exts(new_exts)

            all_exts = safe_exts | new_exts

            lookatme.contrib.load_contribs(
                all_exts,
                safe_exts,
                self.ignore_ext_failure,
            )

        theme = self.meta.get("theme", self.cli_theme or "dark")
        self.theme_mod = __import__("lookatme.themes." + theme, fromlist=[theme])

        self.styles = lookatme.config.set_global_style_with_precedence(
            self.theme_mod,
            self.meta.get("styles", {}),
        )

        self.initial_load_complete = True

    def warn_exts(self, exts):
        """Warn about source-provided extensions that are to-be-loaded"""
        if len(exts) == 0 or self.no_ext_warn:
            return

        warning = lookatme.ascii_art.WARNING
        print("\n".join(["    " + x for x in warning.split("\n")]))

        print(
            "New extensions required by {!r} are about to be loaded:\n".format(
                self.input_filename
            )
        )
        for ext in exts:
            print("  - {!r}".format("lookatme.contrib." + ext))
        print("")

        if not lookatme.prompt.yes("Are you ok with attempting to load them?"):
            print("Bailing due to unacceptance of source-required extensions")
            exit(1)

    def to_html(self, html_output_dir: str, options: Optional[Dict] = None):
        _options = {}
        _options.update(DEFAULT_HTML_OPTIONS)
        _options.update(options or {})
        slides_html, slides_titles = self._create_html(_options["width"])

        html.create_html_output(
            output_dir=html_output_dir,
            slides_html=slides_html,
            slides_titles=slides_titles,
            title_category_delim=_options["title_delim"],
        )

    def _create_html(
        self, width: int = 150
    ) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, Optional[urwid.Canvas]]]]:
        self.tui = lookatme.tui.create_tui(self, start_slide=0, no_threads=True)
        self.tui.update()
        ctx = html.HtmlContext()

        # header, body, footer contents, not wrapped in divs with classes
        # yet
        raw_slides_html: List[Tuple[str, str, str]] = []
        titles: List[Tuple[str, Optional[urwid.Canvas]]] = []
        for slide_idx, slide in enumerate(self.slides):
            titles.append(slide.get_title(self.tui.ctx))
            self.tui.set_slide_idx(slide_idx)

            header, body, footer = self.tui.render_without_scrollbar(width)
            classname = "slide"
            if slide_idx != 0:
                classname += " hidden"

            html.canvas_to_html(ctx, header)
            header_html = ctx.get_html_consumed()

            html.canvas_to_html(ctx, body)
            body_html = ctx.get_html_consumed()

            html.canvas_to_html(ctx, footer)
            footer_html = ctx.get_html_consumed()

            raw_slides_html.append((header_html, body_html, footer_html))

        return raw_slides_html, titles

    def run(self, start_slide=0):
        """Run the presentation!"""
        self.tui = lookatme.tui.create_tui(
            self, start_slide=start_slide, no_threads=self.no_threads
        )
        self.tui.run()

    def get_tui(self) -> lookatme.tui.MarkdownTui:
        if self.tui is None:
            raise ValueError("Tui has not been set, has the presentation been run yet?")
        return self.tui
