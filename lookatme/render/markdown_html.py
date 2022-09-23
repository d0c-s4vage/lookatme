"""
This module attempts to parse basic html
"""


from __future__ import annotations
import re
from typing import Dict, Optional
from html.parser import HTMLParser


from lookatme.render.context import Context
from lookatme.widgets.clickable_text import ClickableText
from lookatme.utils import overwrite_spec, spec_from_style, pile_or_listbox_add


STYLE_MATCHER = re.compile(r"""
    (?P<key>[a-z0-9_-]+)
        \s*:\s*
    (?P<value>[^\s;]*);?
""", re.VERBOSE | re.MULTILINE | re.IGNORECASE)


class LookatmeHTMLParser(HTMLParser):
    def __init__(self, ctx: Context, markdown_inline):
        super(self.__class__, self).__init__()
        self.ctx = ctx
        self.inline = markdown_inline
        self.queued_data = []
    
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict(attrs)
        style = self._parse_style(attrs.get("style", ""))

        spec = None
        spec_styles = {
            "fg": style.get("color", ""),
            "bg": style.get("background-color", ""),
        }
        if len(spec_styles) > 0:
            spec = spec_from_style(spec_styles)

        if tag == "b":
            spec = overwrite_spec(spec, spec_from_style("bold"))
        elif tag == "i":
            spec = overwrite_spec(spec, spec_from_style("italics"))
        elif tag == "blink":
            spec = overwrite_spec(spec, spec_from_style("blink"))
        elif tag == "em":
            spec = overwrite_spec(spec, spec_from_style("standout"))
        elif tag == "u":
            spec = overwrite_spec(spec, spec_from_style("underline"))
        elif tag == "pre":
            self.ctx.literal_push()
        elif tag == "br":
            self.ctx.literal_push()
            self.handle_data("-")
            self.ctx.literal_pop()

        self.ctx.tag_push(tag, spec)
    
    def handle_endtag(self, tag):
        if tag == self.ctx.tag:
            if tag == "pre":
                self.ctx.literal_pop()
            self.ctx.tag_pop()
    
    def handle_data(self, data):
        token = {
            "type": "text",
            "text": data,
        }
        res = self.inline.render_text(token, self.ctx)
        pile_or_listbox_add(self.ctx.container, ClickableText(res))

    def _parse_style(self, style_contents):
        """Parse the style contents
        """
        res = {}
        for style_match in STYLE_MATCHER.finditer(style_contents):
            info = style_match.groupdict()
            res[info["key"]] = info["value"]
        return res


# ATTR_MATCHER = re.compile(r"""
#     (?P<attr>[a-z0-9-]+)
#     \s*=\s*(
#         '(?P<single_quote>[^']*)'
#         |
#         "(?P<double_quote>[^"]*)"
#     )
# """, re.VERBOSE | re.MULTILINE | re.IGNORECASE)
# 
# OPEN_TAG_MATCHER = re.compile(r"""
#     ^
#     <(?P<tag>[a-z-]+)
#         (?P<attrs>(\s+{ATTR_MATCHER})*)
#     \s*>
#     $
# """.format(ATTR_MATCHER=ATTR_MATCHER.pattern), re.VERBOSE | re.MULTILINE | re.IGNORECASE)
# 
# 
# CLOSE_TAG_MATCHER = re.compile(r'</(?P<tag>[a-z]+)>')
# 
# 
# class Tag:
#     @classmethod
#     def parse_tag(cls, text: str) -> Optional[Tag]:
#         """Return a new Tag instance or None after parsing the text
#         """
#         if text.startswith("</"):
#             match = CLOSE_TAG_MATCHER.match(text)
#             if match is None:
#                 return None
#             match_info = match.groupdict()
#             return cls(tag_name=match_info["tag"], is_open=False)
#         
#         match = OPEN_TAG_MATCHER.match(text)
#         if match is None:
#             return None
# 
#         match_info = match.groupdict()
#         tag_name = match_info["tag"]
# 
#         attrs_text = match_info["attrs"]
#         attrs = {}
# 
#         for match in ATTR_MATCHER.finditer(attrs_text):
#             info = match.groupdict()
# 
#             attr_name = info["attr"]
#             val = info.get("single_quote", None) or info.get("double_quote")
#             attrs[attr_name] = val
# 
#         style = None
#         if "style" in attrs:
#             style = cls._parse_style(attrs["style"])
# 
#         return cls(tag_name=tag_name, is_open=True, attrs=attrs, style=style)
# 
#     @classmethod
# 
#     def __init__(self, tag_name: str, is_open: bool, attrs: Optional[Dict[str, str]] = None, style=None):
#         """Stores information about a tag and its attributes
#         """
#         self.is_open = is_open
#         self.name = tag_name
#         self.attrs = attrs or {}
#         self.style = style or {}
