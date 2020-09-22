"""
Defines Presentation specific objects
"""


import mistune
import os
import threading
import time


import lookatme.config
import lookatme.contrib
from lookatme.parser import Parser
import lookatme.themes
import lookatme.tui
from lookatme.utils import dict_deep_update


class Presentation(object):
    """Defines a presentation
    """
    def __init__(self, input_stream, theme, style_override=None, live_reload=False,
                 single_slide=False):
        """Creates a new Presentation

        :param stream input_stream: An input stream from which to read the
            slide data
        """
        self.input_filename = None
        if hasattr(input_stream, "name"):
            lookatme.config.SLIDE_SOURCE_DIR = os.path.dirname(input_stream.name)
            self.input_filename = input_stream.name

        self.style_override = style_override
        self.live_reload = live_reload
        self.tui = None
        self.single_slide = single_slide

        self.theme_mod = __import__("lookatme.themes." + theme, fromlist=[theme])

        if self.live_reload:
            self.reload_thread = threading.Thread(target=self.reload_watcher)
            self.reload_thread.daemon = True
            self.reload_thread.start()

        self.reload(data=input_stream.read())

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
                    self.tui.reload()
                    self.tui.loop.draw_screen()
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
            with open(self.input_filename, "r") as f:
                data = f.read()

        parser = Parser(single_slide=self.single_slide)
        self.meta, self.slides = parser.parse(data)
        lookatme.contrib.load_contribs(self.meta.get("extensions", []))

        self.styles = lookatme.themes.ensure_defaults(self.theme_mod)
        dict_deep_update(self.styles, self.meta.get("styles", {}))

        # now apply any command-line style overrides
        if self.style_override is not None:
            self.styles["style"] = self.style_override

        lookatme.config.STYLE = self.styles

    def run(self, start_slide=0):
        """Run the presentation!
        """
        self.tui = lookatme.tui.create_tui(self, start_slide=start_slide)
        self.tui.run()
