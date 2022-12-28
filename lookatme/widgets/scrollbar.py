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

        self.slider_top_chars = ["⡀", "⣀", "⣠", "⣤", "⣦", "⣶", "⣾", "⣿"]
        self.slider_bottom_chars = ["⠈", "⠉", "⠋", "⠛", "⠻", "⠿", "⡿", "⣿"]

        self.slider_fill_char = "⣿"
        self.slider_spec: urwid.AttrSpec = SmartAttrSpec("#4c4c4c", "")
        self.gutter_fill_char = "▕"
        self.gutter_spec: urwid.AttrSpec = SmartAttrSpec("#2c2c2c", "")

        self._listbox_widget_size_cache: Optional[
            Tuple[List[Tuple[int, int, int]], Tuple, bool, int]
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
        if not self.slider_top_chars:
            self.slider_top_chars.append(self.slider_fill_char)
        if not self.slider_bottom_chars:
            self.slider_bottom_chars.append(self.slider_fill_char)

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
            slider_end_char = self.slider_bottom_chars[
                int(slider_end_val // (1.0 / len(self.slider_bottom_chars)))
            ]

        slider_start_idx_f = slider_end_idx_f - slider_height
        slider_start_val = 1.0 - (slider_start_idx_f - math.floor(slider_start_idx_f))

        if slider_start_val == 1.0:
            slider_start_char = ""
        else:
            fill_count -= slider_start_val
            slider_start_char = self.slider_top_chars[
                int(slider_start_val // (1.0 / len(self.slider_top_chars)))
            ]

        slider_start_idx = math.floor(slider_start_idx_f)
        slider_end_idx = math.ceil(slider_end_idx_f)

        slider_chars = "{}{}{}".format(
            slider_start_char,
            self.slider_fill_char * round(fill_count),
            slider_end_char,
        )

        scroll_text = [
            (
                self.gutter_spec,
                "\n".join(self.gutter_fill_char * slider_start_idx),
            ),
            (self.slider_spec, "\n".join(slider_chars)),
            (
                self.gutter_spec,
                "\n".join(self.gutter_fill_char * (total_chars - slider_end_idx)),
            ),
        ]

        return urwid.Text(scroll_text).render((1,), False)

    def _get_listbox_visible_scroll_range(self) -> Tuple[int, int, int, int]:
        """Return a tuple containing: (visible_start_idx, visible_stop_idx, total_rows)"""
        # we're assuming that the 1 char for the scrollbar is already taken
        # out
        size = self.listbox._last_size  # type: ignore
        height = size[1]

        widget_sizes = self._get_listbox_widget_sizes(size, self.listbox._last_focus)
        # using calculate_visible has turned out to be the most reliable way
        # to determine the bounds of the current view of the ListBox. Other
        # ways had problems when the screen is resized (e.g., scroll to the
        middle, top, bottom = self.listbox.calculate_visible(size, True)

        # from urwid's source:
        #         *middle*
        #             (*row offset*(when +ve) or *inset*(when -ve),
        #             *focus widget*, *focus position*, *focus rows*,
        #             *cursor coords* or ``None``)
        row_offset, focus_widget, focus_pos, focus_rows, cursor = middle
        top_trim, top_widgets = top

        if len(top_widgets) > 0:
            # from urwid's source:
            #         *top*
            #             (*# lines to trim off top*,
            #             list of (*widget*, *position*, *rows*) tuples above focus
            #             in order from bottom to top)
            top_w, top_pos, top_rows = top_widgets[-1]
            before = widget_sizes[top_pos][1] + top_trim
        else:
            before = widget_sizes[focus_pos][1] + abs(row_offset)

        total = widget_sizes[-1][-1]
        after = total - before - height

        return before, height, after, total

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
        total = 0
        for widget in self.listbox.body:
            w_rows = widget.rows((size[0],))
            widget_sizes.append((w_rows, total, total + w_rows))
            total += w_rows

        self._listbox_widget_size_cache = (widget_sizes, size, focus, curr_body_id)

        return widget_sizes

    def should_display(self, size, focus: bool = False):
        # will return ['top', 'bottom'] if both ends of the content are visible
        return len(self.listbox.ends_visible(size, focus)) != 2
