"""
Defines Presentation specific objects
"""


import os
import threading
import time

import lookatme.ascii_art
import lookatme.config
import lookatme.contrib
import lookatme.prompt
import lookatme.themes
import lookatme.tui
from lookatme.parser import Parser
from lookatme.tutorial import tutor


@tutor(
    "general",
    "intro",
    r"""
    `lookatme` is a terminal-based markdown presentation tool.

    That means that you can:

     | Write                 | Render          | Use                            |
     |-----------------------|-----------------|--------------------------------|
     | basic markdown slides | in the terminal | anywhere with markdown support |

    > **NOTE** `l | j | right arrow` advance the slides
    >
    > **NOTE** `q` quits
    """,
    order=0,
)
class Presentation(object):
    """Defines a presentation
    """

    def __init__(self, input_stream, theme, style_override=None, live_reload=False,
                 single_slide=False, preload_extensions=None, safe=False,
                 no_ext_warn=False, ignore_ext_failure=False):
        """Creates a new Presentation

        :param stream input_stream: An input stream from which to read the
            slide data
        """
        self.preload_extensions = preload_extensions or []
        self.input_filename = None
        if hasattr(input_stream, "name"):
            lookatme.config.SLIDE_SOURCE_DIR = os.path.dirname(
                input_stream.name)
            self.input_filename = input_stream.name

        self.style_override = style_override
        self.live_reload = live_reload
        self.tui = None
        self.single_slide = single_slide
        self.safe = safe
        self.no_ext_warn = no_ext_warn
        self.ignore_ext_failure = ignore_ext_failure
        self.initial_load_complete = False

        self.theme_mod = __import__(
            "lookatme.themes." + theme, fromlist=[theme])

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
        self.meta, self.slides = parser.parse(data)

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

        self.styles = lookatme.config.set_global_style_with_precedence(
            self.theme_mod,
            self.meta.get("styles", {}),
            self.style_override,
        )

        self.initial_load_complete = True

    def warn_exts(self, exts):
        """Warn about source-provided extensions that are to-be-loaded
        """
        if len(exts) == 0 or self.no_ext_warn:
            return

        warning = lookatme.ascii_art.WARNING
        print("\n".join(["    " + x for x in warning.split("\n")]))

        print("New extensions required by {!r} are about to be loaded:\n".format(
            self.input_filename
        ))
        for ext in exts:
            print("  - {!r}".format("lookatme.contrib." + ext))
        print("")

        if not lookatme.prompt.yes("Are you ok with attempting to load them?"):
            print("Bailing due to unacceptance of source-required extensions")
            exit(1)

    def run(self, start_slide=0):
        """Run the presentation!
        """
        self.tui = lookatme.tui.create_tui(self, start_slide=start_slide)
        self.tui.run()

    def get_tui(self) -> lookatme.tui.MarkdownTui:
        if self.tui is None:
            raise ValueError(
                "Tui has not been set, has the presentation been run yet?")
        return self.tui
