"""
This module attempts to parse basic html
"""


from __future__ import annotations
import marko
import re
from typing import Dict, Optional
from html.parser import HTMLParser
import urwid
from typing import List, Tuple, Any


import lookatme.config
from lookatme.render.context import Context
from lookatme.widgets.clickable_text import ClickableText
from lookatme.utils import overwrite_spec, spec_from_style, pile_or_listbox_add
import lookatme.parser


class LookatmeHTMLParser(HTMLParser):
    def __init__(self, ctx: Context):
        import lookatme.render.markdown_block as block
        import lookatme.render.markdown_inline as inline

        super(self.__class__, self).__init__()
        self._log = lookatme.config.LOG.getChild("LookatmeHTMLParser")
        self.ctx = ctx
        self.block = block
        self.inline = inline
        self.root = {"type": "root_html", "children": [], "tag": "root"}
        self.token_stack: List[Dict[str, Any]] = [self.root]

    @property
    def parent(self) -> Dict[str, Any]:
        return self.token_stack[-1]

    def token_push(self, token: Dict[str, Any]):
        self.parent["children"].append(token)
        self.token_stack.append(token)

    def token_pop(self, tag: str):
        if self.parent["tag"] != tag:
            raise ValueError("Mismatching open <{!r}> and close </{!r}> tags".format(
                self.parent["tag"],
                tag,
            ))
        self.token_stack.pop()

    def parse(self, data):
        self.feed(data)
        return self.root["children"]

    def _safe_tag(self, tag):
        return re.sub(r'[^a-zA-Z_]', '', tag)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        if attrs is None:
            attrs = []

        tag = self._safe_tag(tag)
        token = {
            "type": "html_tag",
            "tag": tag,
            "attrs": dict(attrs),
            "style": {},
            "children": [],
        }

        style_data = token["attrs"].get("style", None)
        if style_data is not None:
            token["style"] = self._parse_style(style_data)

        self.token_push(token)

    def handle_endtag(self, tag: str):
        self.token_pop(tag)

    def handle_data(self, data: str):
        """
        """
        # block elements
        if self.parent["tag"] in ("div", "ul", "ol", "li"):
            self.parent["children"] += lookatme.parser.md_to_tokens(data)
        # inline elements
        else:
            self.parent["children"] += lookatme.parser.md_to_tokens_inline(data)

    def _parse_style(self, style_contents):
        """Parse the style contents
        """
        res = {}
        for style_match in STYLE_MATCHER.finditer(style_contents):
            info = style_match.groupdict()
            res[info["key"]] = info["value"]
        return res


class LookatmeHTMLParserOld(HTMLParser):
    def __init__(self, ctx: Context):
        import lookatme.render.markdown_block as block
        import lookatme.render.markdown_inline as inline

        super(self.__class__, self).__init__()
        self._log = lookatme.config.LOG.getChild("LookatmeHTMLParser")
        self.ctx = ctx
        self.block = block
        self.inline = inline
        self.queued_data = []

    def record_as_tokens(self):
        """
        """
        self.recording = True
        self.recording_stack = []
    
    def handle_starttag(self, tag, attrs):
        self.ctx.log_debug("open tag: {!r} attrs: {!r}".format(tag, attrs))

        if self.recording:
            self.record_tag_as_token(tag, attrs)
            return

        tag = tag.lower()
        attrs = dict(attrs)
        style = self._parse_style(attrs.get("style", ""))

        spec = None
        text_only_spec = False
        display = TagDisplay.INLINE
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
            text_only_spec = True
        elif tag == "u":
            spec = overwrite_spec(spec, spec_from_style("underline"))
        elif tag == "br":
            self.ctx.inline_push("\n")
        elif tag == "div":
            display = TagDisplay.BLOCK
        elif tag == "p":
            display = TagDisplay.BLOCK
        elif tag == "ul" or tag == "ol":
            self.recording = True
            self.recording_stack.append({
                "type": "list",
                "ordered": tag == "ol",
                "children": [],
            })
        elif tag == "details":
            # TODO
            pass
        elif tag == "summary":
            # TODO
            pass

        self.ctx.tag_push(tag, spec, text_only_spec, display)

        # do this *after* we've added the spec to the context
        if tag == "div":
            #new_container = self.ctx.wrap_widget(urwid.Pile([]))
            #pile_or_listbox_add(self.ctx.container, new_container)
            #self.ctx.container_push(new_container)
            #self.ctx.attr_map_spec_push(spec)
            pass
    
    def handle_endtag(self, tag):
        self.ctx.log_debug("close tag: {!r}".format(tag))
        if self.recording:
            self.record_tag_as_token(tag, close=True)

        if tag == self.ctx.tag:
            self.ctx.tag_pop()
        if tag == "div":
            #self.ctx.container_pop()
            #self.ctx.attr_map_spec_pop()
            pass
    
    def handle_data(self, data):
        self.ctx.log_debug("handle_data: TAG: {!r}, data: {!r}".format(self.ctx.tag, data))
        if self.recording:
            self.record_data_as_token(data)

        if not self.ctx.is_literal:
            data = data.strip()
        if len(data) == 0:
            return
        
        if self.ctx.tag == "style":
            self._handle_style_data(data)
            return

        tokens = lookatme.parser.md_to_tokens(data)
        lookatme.parser.debug_print_tokens(tokens, level=self.ctx.level)

        # if we don't do this, then the first text following a tag will NOT
        # be inline, it will be a new paragraph
        #
        # E.g. he<span>ll</span>o would be rendered as three paragraphs
        if len(tokens) > 0 and isinstance(tokens[0], marko.block.Paragraph):
            paragraph_token = tokens[0]
            self.inline.render_all(paragraph_token.children, self.ctx)
            tokens = tokens[1:]

        self.block.render_all(tokens, self.ctx)

    def _handle_style_data(self, data):
        """Only parse basic CSS data - nothing fancy! All selectors are assumed
        to match: \.?[a-zA-Z-_0-9]+\s*{\s*[^}]*}.
        """
        res = {}
        for selector_match in SELECTOR_MATCHER.finditer(data):
            __import__("pdb").set_trace()
        return res

ATTR_MATCHER = re.compile(r"""
    (?P<attr>[a-z0-9-]+)
    \s*=\s*(
        '(?P<single_quote>[^']*)'
        |
        "(?P<double_quote>[^"]*)"
    )
""", re.VERBOSE | re.MULTILINE | re.IGNORECASE)

OPEN_TAG_MATCHER = re.compile(r"""
    ^
    <(?P<tag>[a-z-]+)
        (?P<attrs>(\s+{ATTR_MATCHER})*)
    \s*(?P<openclose>/)?>
    $
""".format(ATTR_MATCHER=ATTR_MATCHER.pattern), re.VERBOSE | re.MULTILINE | re.IGNORECASE)


CLOSE_TAG_MATCHER = re.compile(r'</(?P<tag>[a-z]+)>')

STYLE_MATCHER = re.compile(r"""
    (?P<key>[a-z0-9_-]+)
        \s*:\s*
    (?P<value>[^\s;]*);?
""", re.VERBOSE | re.MULTILINE | re.IGNORECASE)


SELECTOR_MATCHER = re.compile(r"""
    (?P<selector>[\.a-zA-Z0-9-_]+)
    \s*
    {
        \s*
        [^}]*
        \s*
    }
""", re.VERBOSE | re.MULTILINE | re.IGNORECASE)


class Tag:
    @classmethod
    def parse(cls, text: str) -> List[Self]:
        """Return a new Tag instance or None after parsing the text
        """
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
        res.append(
            cls(tag_name=tag_name, is_open=True, attrs=attrs, style=style)
        )
        if match_info["openclose"] is not None:
            res.append(
                cls(tag_name=tag_name, is_open=False, attrs=attrs, style=style)
            )
        return res

    @classmethod
    def parse_style(cls, style_contents):
        """Parse the style contents
        """
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
            style: Optional[Dict[str, str]] = None
        ):
        """Stores information about a tag and its attributes
        """
        self.is_open = is_open
        self.name = tag_name
        self.attrs = attrs or {}
        self.style = style or {}

