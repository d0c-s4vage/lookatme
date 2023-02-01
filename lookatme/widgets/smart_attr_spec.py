import urwid


class SmartAttrSpec(urwid.AttrSpec):
    preserve_spaces: bool = False

    def __init__(self, fg, bg):
        """An attr spec that chooses the right color depth"""
        super().__init__(fg, bg, 2**24)
