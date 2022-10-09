"""
This module attempts to parse basic html
"""


from __future__ import annotations

import re
from typing import Dict, List, Optional

ATTR_MATCHER = re.compile(
    r"""
    (?P<attr>[a-z0-9-]+)
    \s*=\s*(
        '(?P<single_quote>[^']*)'
        |
        "(?P<double_quote>[^"]*)"
    )
""",
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)

OPEN_TAG_MATCHER = re.compile(
    r"""
    ^
    <(?P<tag>[a-z-]+)
        (?P<attrs>(\s+{ATTR_MATCHER})*)
    \s*(?P<openclose>/)?>
    $
""".format(
        ATTR_MATCHER=ATTR_MATCHER.pattern
    ),
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)


CLOSE_TAG_MATCHER = re.compile(r"</(?P<tag>[a-z]+)>")

STYLE_MATCHER = re.compile(
    r"""
    (?P<key>[a-z0-9_-]+)
        \s*:\s*
    (?P<value>[^\s;]*);?
""",
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)


SELECTOR_MATCHER = re.compile(
    r"""
    (?P<selector>[\.a-zA-Z0-9-_]+)
    \s*
    {
        \s*
        [^}]*
        \s*
    }
""",
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)


class Tag:
    @classmethod
    def parse(cls, text: str) -> List[Tag]:
        """Return a new Tag instance or None after parsing the text"""
        if text.startswith("</"):
            match = CLOSE_TAG_MATCHER.match(text)
            if match is None:
                return []
            match_info = match.groupdict()
            return [cls(tag_name=match_info["tag"], is_open=False)]

        match = OPEN_TAG_MATCHER.match(text)
        if match is None:
            return []

        match_info = match.groupdict()
        tag_name = match_info["tag"]

        attrs_text = match_info["attrs"]
        attrs = {}

        for match in ATTR_MATCHER.finditer(attrs_text):
            info = match.groupdict()

            attr_name = info["attr"]
            val = info.get("single_quote", None) or info.get("double_quote")
            attrs[attr_name] = val

        style = None
        if "style" in attrs:
            style = cls.parse_style(attrs["style"])

        res = []
        res.append(cls(tag_name=tag_name, is_open=True, attrs=attrs, style=style))
        if match_info["openclose"] is not None:
            res.append(cls(tag_name=tag_name, is_open=False, attrs=attrs, style=style))
        return res

    @classmethod
    def parse_style(cls, style_contents):
        """Parse the style contents"""
        res = {}
        for style_match in STYLE_MATCHER.finditer(style_contents):
            info = style_match.groupdict()
            res[info["key"]] = info["value"]
        return res

    def __init__(
        self,
        tag_name: str,
        is_open: bool,
        attrs: Optional[Dict[str, str]] = None,
        style: Optional[Dict[str, str]] = None,
    ):
        """Stores information about a tag and its attributes"""
        self.is_open = is_open
        self.name = tag_name
        self.attrs = attrs or {}
        self.style = style or {}
