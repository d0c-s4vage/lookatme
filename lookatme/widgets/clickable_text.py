"""
This module contains code for ClickableText
"""


import platform
import subprocess

import urwid
from urwid.util import is_mouse_press

import lookatme.config
from lookatme.widgets.smart_attr_spec import SmartAttrSpec


class LinkIndicatorSpec(SmartAttrSpec):
    """Used to track a link within an urwid.Text instance"""

    def __init__(self, link_target, orig_spec, link_type: str = "link"):
        """Create a new LinkIndicator spec from an existing urwid.AttrSpec

        :param str link_target: The target url for the link
        """
        self.link_target = link_target
        self.link_type = link_type

        super().__init__(orig_spec.foreground, orig_spec.background)

    def new_for_spec(self, new_spec):
        """Create a new LinkIndicatorSpec with the same link information but
        new AttrSpec
        """
        return LinkIndicatorSpec(self.link_target, new_spec, self.link_type)


class ClickableText(urwid.Text):
    """Allows clickable/changing text to be part of the Text() contents"""

    signals = ["click", "change"]

    def __init__(self, markup, *args, **kwargs):
        self._log = lookatme.config.get_log().getChild("ClickableText")

        super(ClickableText, self).__init__(markup, *args, **kwargs)

    def mouse_event(self, size, event, button, x, y, focus):
        """Handle mouse events!"""
        if button != 1 or not is_mouse_press(event):
            return False

        total_offset = (y * size[0]) + x

        raw_text, chunk_stylings = self.get_text()
        rendered = self.render(size).text

        # TODO: this won't work too well with wrapped text!
        curr_offset = rendered[0].decode().find(raw_text)

        found_style = None

        for info in chunk_stylings:
            style, length = info
            if curr_offset < total_offset <= curr_offset + length:
                found_style = style
                break
            curr_offset += length

        if found_style is None or not isinstance(found_style, LinkIndicatorSpec):
            self._emit("click")
            return True

        this_sys = platform.system()
        link_cmd = {
            "Linux": ["xdg-open"],
            "Darwin": ["open"],
            "Windows": ["start"],
        }.get(this_sys, None)

        if link_cmd is None:
            self._log.debug(
                "No link-opening command defined yet for {!r}".format(this_sys)
            )
            return True

        found_link = found_style.link_target
        subprocess.Popen(
            link_cmd + [found_link], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )

        return True
