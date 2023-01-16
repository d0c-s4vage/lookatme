"""
Replaces an urwid.BaseScreen with one that renders the terminal into html
files.
"""


from typing import List, Optional, Tuple


import urwid


class KeypressEmulatorBase:
    def get_next(self) -> Optional[Tuple[int, int, List[str]]]:
        raise NotImplementedError("get_next is not implemented")

    def get_default_delay(self) -> int:
        raise NotImplementedError("get_default_delay is not implemented")


class HtmlScreenshotScreen(urwid.BaseScreen):
    """ """

    def __init__(
        self,
        draw_screen_callback,
        keys: Optional[KeypressEmulatorBase] = None,
        cols: int = 150,
        rows: int = 100,
    ):
        super().__init__()

        self.keys = keys
        self.cols = cols
        self.rows = rows
        self._draw_screen_callback = draw_screen_callback

        self.last_info = {
            "render_count": 0,
            "key_idx": 0,
            "key": [""],
            "delay": 0 if not keys else keys.get_default_delay(),
        }

    def set_terminal_properties(self, *args, **kwargs):
        pass

    def set_mouse_tracking(self, enable=True):
        pass

    def set_input_timeouts(self, *args):
        pass

    def reset_default_terminal_palette(self, *args):
        pass

    def clear(self):
        pass

    def get_cols_rows(self):
        return (self.cols, self.rows)

    def get_input(self, raw_keys=False):
        if not self.keys:
            raise urwid.ExitMainLoop()

        next_key_info = self.keys.get_next()
        if next_key_info is None:
            raise urwid.ExitMainLoop()

        last_key_idx, last_delay, last_key = next_key_info
        self.last_info.update(
            {
                "key_idx": last_key_idx,
                "delay": last_delay,
                "key": last_key,
            }
        )
        if raw_keys:
            return (last_key, [])

        return last_key

    def draw_screen(self, size: Tuple[int, int], canvas: urwid.Canvas):
        self._draw_screen_callback(self.last_info, canvas)
        self.last_info["render_count"] += 1
