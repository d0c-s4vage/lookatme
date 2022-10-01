"""
This module contains code for ClickableText
"""


import urwid
from urwid.util import is_mouse_press


import lookatme.config as config
from lookatme.utils import spec_from_style, row_text


class LinkIndicatorSpec(urwid.AttrSpec):
    """Used to track a link within an urwid.Text instance
    """
    def __init__(self, link_label, link_target, orig_spec):
        """Create a new LinkIndicator spec from an existing urwid.AttrSpec

        :param str link_label: The label for the link
        :param str link_target: The target url for the link
        """
        self.link_label = link_label
        self.link_target = link_target

        urwid.AttrSpec.__init__(self, orig_spec.foreground, orig_spec.background)


class ClickableText(urwid.Text):
    """Allows clickable/changing text to be part of the Text() contents
    """

    signals = ["click", "change"]

    def mouse_event(self, size, event, button, x, y, focus):
        """Handle mouse events!
        """
        if button != 1 or not is_mouse_press(event):
            return False

        rendered = self.render(size).content()
        total_text = b"\n".join(row_text(x) for x in rendered)

        total_offset = (y * size[0]) + x

        text, chunk_stylings = self.get_text()
        curr_offset = 0

        found_style = None
        found_text = None
        found_idx = 0
        found_length = 0

        for idx, info in enumerate(chunk_stylings):
            style, length = info
            if curr_offset < total_offset <= curr_offset + length:
                found_text = text[curr_offset:curr_offset + length]
                found_style = style
                found_idx = idx
                found_length = length
                break
            curr_offset += length

        if found_style is None or not isinstance(found_style, LinkIndicatorSpec):
            self._emit('click')
            return True
        
        # it's a link, so change the text and update the RLE!
        if found_text == found_style.link_label:
            new_text = found_style.link_target
        else:
            new_text = found_style.link_label
        text = text[:curr_offset] + new_text + text[curr_offset+found_length:]
        new_rle = len(new_text)

        chunk_stylings[found_idx] = (found_style, new_rle)

        self._text = text
        self._attrib = chunk_stylings
        self._invalidate()

        self._emit("change")
        
        return True
