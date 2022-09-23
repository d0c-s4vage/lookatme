import urwid


class SmartAttrSpec(urwid.AttrSpec):
    def __init__(self, fg, bg):
        """An attr spec that chooses the right color depth
        """
        super(self.__class__, self).__init__(fg, bg, 2**24)
