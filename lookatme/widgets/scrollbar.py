import math
from typing import List, Optional, Tuple


import urwid
from urwid.signals import connect_signal


import lookatme.config as config
from lookatme.widgets.smart_attr_spec import SmartAttrSpec


class Scrollbar(urwid.Widget):
    """A scrollbar that reflects the current scroll state of a list box.
    Non-selectable, non-interactive, informative only. Especially useful as
    an overlay or a box column so that you can have additional padding around
    your ListBox.
    """

    _sizing = frozenset([urwid.BOX])
    _selectable = False
    ignore_focus = True

    def __init__(self, listbox: urwid.ListBox):
        super().__init__()

        self.top_parts = ["⡀", "⣀", "⣠", "⣤", "⣦", "⣶", "⣾", "⣿"]
        self.bottom_parts = ["⠈", "⠉", "⠋", "⠛", "⠻", "⠿", "⡿", "⣿"]

        self.scrollbar_slider_fill = "⣿"
        self.scrollbar_slider_spec = SmartAttrSpec("#4c4c4c", "")
        self.scrollbar_gutter_fill = "▕"
        self.scrollbar_gutter_spec = SmartAttrSpec("#2c2c2c", "")

        self._listbox_widget_size_cache: Optional[
            Tuple[List[int], Tuple, bool, int]
        ] = None

        self.listbox = listbox
        connect_signal(self.listbox.body, "modified", self._invalidate)
        self.listbox.render_orig = self.listbox.render
        self.listbox.render = self._listbox_render

    def _listbox_invalidate(self):
        self.listbox._invalidate_orig()
        self._invalidate()

    def _listbox_render(self, size, focus: bool = False):
        self.listbox._last_size = size
        self.listbox._last_focus = focus
        res = self.listbox.render_orig(size, focus)
        self._invalidate()
        return res

    def render(self, size: Tuple[int, int], focus: bool = False):
        """Please use `needs_scrollbar()` if manually deciding to render the
        Scrollbar (e.g. if you're overlaying the rendered results onto a canvas)
        """
        before, visible, after, total = self._get_listbox_visible_scroll_range()
        scroll_percent = before / float(before + after)
        scroll_percent = max(0.0, scroll_percent)

        _, height = size
        total_chars = height

        slider_height = max(height * float(visible) / total, 2.0)
        fill_count = slider_height

        slider_end_idx_f = (
            slider_height + (total_chars - slider_height) * scroll_percent
        )
        slider_end_val = slider_end_idx_f - math.floor(slider_end_idx_f)
        if slider_end_val == 0.0:
            slider_end_char = ""
        else:
            fill_count -= slider_end_val
            slider_end_char = self.bottom_parts[
                int(slider_end_val // (1.0 / len(self.bottom_parts)))
            ]

        slider_start_idx_f = slider_end_idx_f - slider_height
        slider_start_val = 1.0 - (slider_start_idx_f - math.floor(slider_start_idx_f))

        if slider_start_val == 1.0:
            slider_start_char = ""
        else:
            fill_count -= slider_start_val
            slider_start_char = self.top_parts[
                int(slider_start_val // (1.0 / len(self.top_parts)))
            ]

        slider_start_idx = math.floor(slider_start_idx_f)
        slider_end_idx = math.ceil(slider_end_idx_f)

        slider_chars = "{}{}{}".format(
            slider_start_char,
            self.scrollbar_slider_fill * int(fill_count),
            slider_end_char,
        )

        scroll_text = [
            (
                self.scrollbar_gutter_spec,
                "\n".join(self.scrollbar_gutter_fill * slider_start_idx),
            ),
            (self.scrollbar_slider_spec, "\n".join(slider_chars)),
            (
                self.scrollbar_gutter_spec,
                "\n".join(self.scrollbar_gutter_fill * (total_chars - slider_end_idx)),
            ),
        ]
        res = urwid.Text(scroll_text).render((1,), False)

        return res

    def _get_listbox_visible_scroll_range(self) -> Tuple[int, int, int, int]:
        """Return a tuple containing: (visible_start_idx, visible_stop_idx, total_rows)"""
        # we're assuming that the 1 char for the scrollbar is already taken
        # out
        size = self.listbox._last_size  # type: ignore
        height = size[1]

        # inset == take rows off of the end of the focus widget
        # offset == take rows off of the start of the focus widget
        focus_offset, focus_inset = self.listbox.get_focus_offset_inset(size)
        focus_widget, _ = self.listbox.body.get_focus()

        # the unseen rows before
        rows_before_focus = 0
        rows_total = 0
        widget_sizes = self._get_listbox_widget_sizes(size, self.listbox._last_focus)
        for widget_idx, widget in enumerate(self.listbox.body):
            if widget == focus_widget:
                rows_before_focus = rows_total
            rows_total += widget_sizes[widget_idx]

        rows_before = rows_before_focus + focus_inset
        rows_before -= focus_offset
        rows_after = rows_total - height - rows_before

        if rows_after < 0:
            # this is a slower calculation than get_focus_offset_inset - sometimes
            # the listbox inset fraction doesn't get updated correctly. Using
            # calculate_visible forces a fresh calculation
            _, top, __ = self.listbox.calculate_visible(size, True)
            focus_inset, _ = top

            rows_before = rows_before_focus + focus_inset
            rows_before -= focus_offset
            rows_after = rows_total - height - rows_before

        return (rows_before, height, rows_after, rows_total)

    def _get_listbox_widget_sizes(self, size, focus):
        curr_body_id = id(self.listbox.body)
        if self._listbox_widget_size_cache is not None:
            (
                cached_widget_sizes,
                cached_size,
                cached_focus,
                cached_body_id,
            ) = self._listbox_widget_size_cache
            if (
                True
                and cached_size == size
                and cached_focus == focus
                and cached_body_id == curr_body_id
            ):
                return cached_widget_sizes

        widget_sizes = []
        for widget in self.listbox.body:
            widget_sizes.append(widget.rows((size[0],)))

        self._listbox_widget_size_cache = (widget_sizes, size, focus, curr_body_id)

        return widget_sizes

    def should_display(self, size, focus: bool = False):
        # will return ['top', 'bottom'] if both ends of the content are visible
        return len(self.listbox.ends_visible(size, focus)) != 2
