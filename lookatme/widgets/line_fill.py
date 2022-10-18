from typing import Optional, Tuple, Union

import urwid


class LineFill(urwid.Widget):
    """Test"""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

    _sizing = frozenset([urwid.BOX, urwid.FLOW])
    _selectable = False
    ignore_focus = True

    def __init__(
        self,
        beg_chars: str,
        fill_char: str,
        end_chars: str,
        beg_spec: Optional[urwid.AttrSpec] = None,
        fill_spec: Optional[urwid.AttrSpec] = None,
        end_spec: Optional[urwid.AttrSpec] = None,
        orientation: str = VERTICAL,
    ):
        """ """
        self.beg_chars = beg_chars
        self.beg_spec = beg_spec

        self.fill_char = fill_char
        self.fill_spec = fill_spec

        self.end_chars = end_chars
        self.end_spec = end_spec

        self.orientation = orientation

        super(self.__class__, self).__init__()

    def rows(self, size: Tuple, focus: bool = False):
        if self.orientation == self.HORIZONTAL:
            return 1
        else:
            raise urwid.WidgetError("VERTICAL LineFill must be used as a box")

    def pack(self, size: Tuple, focus: bool = False):
        if self.orientation == self.VERTICAL:
            return (1, size[1])
        else:
            return (size[0], 1)

    def render(self, size: Tuple, focus: bool = False):
        if self.orientation == self.HORIZONTAL:
            return self._render_horizontal(size, focus)
        else:
            return self._render_vertical(size, focus)

    def _render_horizontal(self, size: Tuple, focus: bool = False):
        maxcols = size[0]
        return urwid.Text(self._get_markups(maxcols)).render(size, focus)

    def _render_vertical(self, size: Tuple, focus: bool = False):
        pile_widgets = []
        maxrows = size[1]
        for markup in self._get_markups(maxrows):
            pile_widgets.append(("pack", urwid.Text(markup)))
        return urwid.Pile(pile_widgets).render(size, focus)

    def _get_markups(self, maxchars: int):
        markups = []
        mid = (maxchars // 2) - 1
        for idx in range(maxchars):
            markup = self._markup(self.fill_spec, self.fill_char)
            if idx <= mid and idx < len(self.beg_chars):
                markup = self._markup(self.beg_spec, self.beg_chars[idx])
            elif idx >= maxchars - len(self.end_chars):
                end_idx = len(self.end_chars) - (maxchars - idx)
                markup = self._markup(self.end_spec, self.end_chars[end_idx])
            markups.append(markup)

        return markups

    def _markup(self, spec: Union[None, urwid.AttrSpec], text: str):
        if spec is None:
            return text

        if (
            isinstance(text, tuple)
            and len(text) == 2
            and isinstance(text[0], urwid.AttrSpec)
        ):
            return text

        return (spec, text)
