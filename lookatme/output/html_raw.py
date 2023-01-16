"""
Output formatter for raw "screenshots" of lookatme as it would appear in a
terminal
"""


from collections import deque
import os
from typing import Any, Dict, List, Optional, Tuple


import urwid


from lookatme.output.base import BaseOutputFormat
from lookatme.pres import Presentation
import lookatme.render.html as html
from lookatme.render.html.screenshot_screen import (
    HtmlScreenshotScreen,
    KeypressEmulatorBase,
)
import lookatme.utils as utils


class KeypressEmulator(KeypressEmulatorBase):
    def __init__(self, keys: List[str], pres, default_delay: int = 500):
        self.keys = deque(keys)
        self.pres = pres
        self.queue = keys
        self.key_idx = 0
        self.default_delay = default_delay

    def get_default_delay(self) -> int:
        return self.default_delay

    def get_next(self) -> Optional[Tuple[int, int, List[str]]]:
        if self.key_idx >= len(self.keys):
            return None

        parts = self.keys[self.key_idx].split(":")
        curr_key = parts[0]
        curr_idx = self.key_idx
        self.key_idx += 1

        delay = self.default_delay if len(parts) == 1 else int(parts[1])

        if curr_key == "scroll-down":
            if self.pres.tui is None:
                return None
            if self.pres.tui.slide_body_scrollbar.scroll_percent != 1.0:
                self.key_idx -= 1
                return (curr_idx, delay, ["down"])
            else:
                return self.get_next()

        elif curr_key == "scroll-up":
            if self.pres.tui.slide_body_scrollbar.scroll_percent != 0.0:
                self.key_idx -= 1
                return (curr_idx, delay, ["up"])
            else:
                return self.get_next()
        else:
            return (curr_idx, delay, [curr_key])


class HtmlRawScreenshotOutputFormat(BaseOutputFormat):
    NAME = "html_raw"
    DEFAULT_OPTIONS = {
        "cols": 100,
        "rows": 30,
        "keys": ["show-all"],
        "render_images": False,
        "delay_default": 1000,
        "delay_scroll": 100,
    }

    def do_format_pres(self, pres: Presentation, output_path: str):
        """ """
        self.output_path = output_path
        keys = self.opt("keys")
        scroll_delay = self.opt("delay_scroll")

        if len(keys) == 1 and keys[0] == "show-all":
            scroll_down = f"scroll-down:{scroll_delay}"
            keys = [scroll_down]
            keys += ["j", scroll_down] * (len(pres.slides) - 1)

        pres.tui_init_sync()
        if pres.tui is None:
            raise RuntimeError("Tui not defined yet")

        pres.tui.loop.screen = HtmlScreenshotScreen(
            self.draw_screen_callback,
            keys=KeypressEmulator(keys, pres, self.opt("delay_default")),
            cols=self.opt("cols"),
            rows=self.opt("rows"),
        )
        pres.tui.run()

    def draw_screen_callback(self, info: Dict[str, Any], canvas: urwid.Canvas):
        render_count = info["render_count"]
        delay = info["delay"]
        key = info["key"]
        output_name = f"screen:{render_count}_delay:{delay}_key:{key[0]}.html"
        self._render_next_frame(canvas, output_name)

    def _render_next_frame(self, canvas: urwid.Canvas, output_name: str):
        ctx = html.HtmlContext()
        html.canvas_to_html(ctx, canvas, render_images=self.opt("render_images"))
        slide_html = ctx.get_html()

        context = {}
        html.add_styles_to_context(context)
        styles = self.render_template("styles.template.css", context)

        context.update(
            {
                "slide": slide_html,
                "styles": styles,
            }
        )

        single_slide_html = self.render_template("single_slide.template.html", context)

        static_dir = os.path.join(os.path.dirname(__file__), "html_static")
        dst_static_dir = os.path.join(self.output_path, "static")
        utils.fs.copy_tree_update(static_dir, dst_static_dir)

        full_path = os.path.join(self.output_path, output_name)
        with open(full_path, "w") as f:
            f.write(single_slide_html)
