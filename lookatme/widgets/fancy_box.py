from typing import Optional

import urwid

from lookatme.widgets.line_fill import LineFill


class FancyBox(urwid.WidgetDecoration, urwid.WidgetWrap):
    """Test"""

    tl_corner = """██━━──
                   ┃
                   │"""
    l_fill = r_fill = "│"
    t_fill = b_fill = "─"
    tr_corner = """──━━██
                        ┃
                        │"""
    bl_corner = """│
                   ┃
                   ██━━──"""

    br_corner = """│
                   ┃
              ──━━██"""

    def __init__(
        self,
        w,
        tl_corner: str = "┌",
        tr_corner: str = "┐",
        bl_corner: str = "└",
        br_corner: str = "┘",
        tl_corner_spec: Optional[urwid.AttrSpec] = None,
        tr_corner_spec: Optional[urwid.AttrSpec] = None,
        bl_corner_spec: Optional[urwid.AttrSpec] = None,
        br_corner_spec: Optional[urwid.AttrSpec] = None,
        t_fill: str = "─",
        b_fill: str = "─",
        l_fill: str = "│",
        r_fill: str = "│",
        t_fill_spec: Optional[urwid.AttrSpec] = None,
        b_fill_spec: Optional[urwid.AttrSpec] = None,
        l_fill_spec: Optional[urwid.AttrSpec] = None,
        r_fill_spec: Optional[urwid.AttrSpec] = None,
        tight: bool = False,
    ):
        """adsf
        adsfadsf
        """
        self.tl_corner = tl_corner
        self.tr_corner = tr_corner
        self.bl_corner = bl_corner
        self.br_corner = br_corner
        self.tl_corner_spec = tl_corner_spec
        self.tr_corner_spec = tr_corner_spec
        self.bl_corner_spec = bl_corner_spec
        self.br_corner_spec = br_corner_spec
        self.t_fill = t_fill
        self.b_fill = b_fill
        self.l_fill = l_fill
        self.r_fill = r_fill
        self.t_fill_spec = t_fill_spec
        self.b_fill_spec = b_fill_spec
        self.l_fill_spec = l_fill_spec
        self.r_fill_spec = r_fill_spec
        self.tight = tight

        final = self._generate(w)

        urwid.WidgetDecoration.__init__(self, final)
        urwid.WidgetWrap.__init__(self, final)

    # flake8: noqa: C901
    def set(
        self,
        tl_corner: Optional[str] = None,
        tr_corner: Optional[str] = None,
        bl_corner: Optional[str] = None,
        br_corner: Optional[str] = None,
        tl_corner_spec: Optional[urwid.AttrSpec] = None,
        tr_corner_spec: Optional[urwid.AttrSpec] = None,
        bl_corner_spec: Optional[urwid.AttrSpec] = None,
        br_corner_spec: Optional[urwid.AttrSpec] = None,
        t_fill: Optional[str] = None,
        b_fill: Optional[str] = None,
        l_fill: Optional[str] = None,
        r_fill: Optional[str] = None,
    ):
        changed = False
        if tl_corner is not None:
            changed = True
            self.tl_corner = tl_corner
        if tr_corner is not None:
            changed = True
            self.tr_corner = tr_corner
        if bl_corner is not None:
            changed = True
            self.bl_corner = bl_corner
        if br_corner is not None:
            changed = True
            self.br_corner = br_corner
        if tl_corner_spec is not None:
            changed = True
            self.tl_corner_spec = tl_corner_spec
        if tr_corner_spec is not None:
            changed = True
            self.tr_corner_spec = tr_corner_spec
        if bl_corner_spec is not None:
            changed = True
            self.bl_corner_spec = bl_corner_spec
        if br_corner_spec is not None:
            changed = True
            self.br_corner_spec = br_corner_spec
        if t_fill is not None:
            changed = True
            self.t_fill = t_fill
        if b_fill is not None:
            changed = True
            self.b_fill = b_fill
        if l_fill is not None:
            changed = True
            self.l_fill = l_fill
        if r_fill is not None:
            changed = True
            self.r_fill = r_fill

        if changed:
            self._generate()

    def _generate(self, w: Optional[urwid.Widget] = None):
        """sdfa
        asdf
        """
        set_w = False
        if w is None:
            set_w = True
            w = self._original_widget

        if w is None:
            raise Exception("w must not be None!")

        tl_hor, tl_ver = self._get_corner_parts(self.tl_corner, 0, left=True)
        bl_hor, bl_ver = self._get_corner_parts(self.bl_corner, -1, left=True)
        tr_hor, tr_ver = self._get_corner_parts(self.tr_corner, 0)
        br_hor, br_ver = self._get_corner_parts(self.br_corner, -1)

        pile = urwid.Pile(
            [
                LineFill(
                    tl_hor,
                    self.t_fill,
                    tr_hor,
                    self.tl_corner_spec,
                    self.t_fill_spec,
                    self.tr_corner_spec,
                    orientation=LineFill.HORIZONTAL,
                ),
                w,
                LineFill(
                    bl_hor,
                    self.b_fill,
                    br_hor,
                    self.bl_corner_spec,
                    self.b_fill_spec,
                    self.br_corner_spec,
                    orientation=LineFill.HORIZONTAL,
                ),
            ]
        )

        if self.tight:
            widget_width = w.pack((400,), False)[0]
            pile_col = (widget_width, pile)
        else:
            pile_col = pile

        final = urwid.Columns(
            [
                (
                    1,
                    LineFill(
                        tl_ver,
                        self.l_fill,
                        bl_ver,
                        self.tl_corner_spec,
                        self.l_fill_spec,
                        self.bl_corner_spec,
                    ),
                ),
                pile_col,
                (
                    1,
                    LineFill(
                        tr_ver,
                        self.r_fill,
                        br_ver,
                        self.tr_corner_spec,
                        self.r_fill_spec,
                        self.br_corner_spec,
                    ),
                ),
            ],
            box_columns=[0, 2],
            focus_column=1,
        )

        if set_w:
            self._w = final
        else:
            return final

    def _get_corner_parts(self, corner_str: str, hor_idx, left=False):
        if corner_str.strip().count("\n") == 0:
            return corner_str[1:], corner_str[0]

        lines = corner_str.split("\n")
        corner_pos = 0 if left else -1
        if hor_idx == 0:
            ver_parts = [lines[hor_idx].strip()[corner_pos]] + lines[1:]
        else:
            ver_parts = corner_str.split("\n")[:-1] + [
                lines[hor_idx].strip()[corner_pos]
            ]

        ver = "".join(map(lambda x: x.strip(), ver_parts))
        hor = corner_str.split("\n")[hor_idx].strip()
        if left:
            hor = hor[1:]
        else:
            hor = hor[:-1]

        return (hor, ver)

    def pack(self, size, focus=False):
        res = list(self._original_widget.pack(size, focus))
        res[0] += 2
        res[1] += 2
        return res
