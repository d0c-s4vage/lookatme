"""
This module renders lookatme slides to HTML
"""


from collections import deque
from contextlib import contextmanager
import re
from typing import Dict, Optional


import urwid


import lookatme.config as config
from lookatme.widgets.clickable_text import LinkIndicatorSpec
import lookatme.utils as utils


class HtmlContext:
    def __init__(self):
        self.output = deque()

    @contextmanager
    def use_tag(
        self,
        tag_name: str,
        classname: Optional[str] = None,
        id: Optional[str] = None,
        style: Optional[Dict[str, str]] = None,
        **other_attrs,
    ):
        attrs = other_attrs

        if classname:
            attrs["class"] = classname
        if id:
            attrs["id"] = id
        if style:
            attrs["style"] = "; ".join(f"{k}: {v}" for k, v in style.items())

        attrs_str = ""
        if attrs:
            attrs_str = " ".join(f'{key}="{val}"' for key, val in attrs.items())
            attrs_str = " " + attrs_str

        self.output.append(f"<{tag_name}{attrs_str}>")
        yield
        self.output.append(f"</{tag_name}>")

    @contextmanager
    def use_spec(self, spec: Optional[urwid.AttrSpec], render_images: bool = True):
        if spec is None:
            yield
            return

        tag = "span"

        extra_attrs = {}
        styles = {}
        swap_fg_bg_colors = False
        for part in spec.foreground.split(","):
            part = part.strip().lower()
            if part.startswith("#"):
                styles["color"] = part
            elif part == "underline":
                decoration = styles.setdefault("text-decoration", "")
                styles["text-decoration"] = decoration + " underline"
            elif part == "blink":
                extra_attrs["classname"] = "blink"
            elif part == "bold":
                styles["font-weight"] = "bold"
            elif part == "italics":
                styles["font-style"] = "italic"
            elif part == "standout":
                swap_fg_bg_colors = True
            elif part == "strikethrough":
                decoration = styles.setdefault("text-decoration", "")
                styles["text-decoration"] = decoration + " strikethrough"

        if isinstance(spec, LinkIndicatorSpec) and render_images:
            if spec.link_type == "link":
                tag = "a"
                extra_attrs["href"] = spec.link_target
                extra_attrs["target"] = "blank"
            elif spec.link_type == "image":
                tag = "img"
                extra_attrs["src"] = spec.link_target

        if spec.background.startswith("#"):
            styles["background-color"] = spec.background

        if swap_fg_bg_colors:
            fg = styles.get("color", "")
            bg = styles.get("background-color", "")
            styles["color"] = bg
            styles["background-color"] = fg

        with self.use_tag(tag, style=styles, **extra_attrs):
            yield

    def write(self, content: str):
        self.output.append(content)

    def get_html(self):
        return "".join(self.output)

    def get_html_consumed(self):
        res = self.get_html()
        self.output = []
        return res


def _sanitize(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _keep_text(text_idx: int, text: str, keep_range: range) -> str:
    text_stop = text_idx + len(text)

    if text_stop < keep_range.start:
        return ""

    if text_idx > keep_range.stop:
        return ""

    start = max(keep_range.start, text_idx)
    stop = min(text_stop, keep_range.stop)

    return text[start - text_idx : stop - text_idx]


def _space_span_replace(match: re.Match) -> str:
    spaces = match.group(0)
    return f"<span style='padding-left: {len(spaces)}ch'></span>"


def canvas_to_html(
    ctx: HtmlContext,
    canvas: urwid.Canvas,
    only_keep: Optional[str] = None,
    render_images: bool = True,
):
    for idx, row in enumerate(canvas.content()):
        only_keep_range = None
        if only_keep:
            start_idx = canvas.text[idx].decode().find(only_keep)
            if start_idx == -1:
                continue
            only_keep_range = range(start_idx, start_idx + len(only_keep))

        text_idx = 0
        for spec, _, text in row:
            text = text.decode()
            if only_keep_range:
                new_text = _keep_text(text_idx, text, only_keep_range)
                text_idx += len(text)
                text = new_text

            text = _sanitize(text)
            if getattr(spec, "preserve_spaces", False):
                text = text.replace(" ", "&nbsp;")
            else:
                text = re.sub(r"( {2,})", _space_span_replace, text)

            if text == "":
                continue

            with ctx.use_spec(spec, render_images=render_images):
                ctx.write(text)

        if idx != len(canvas.text) - 1:
            ctx.write("<br/>\n")


def add_styles_to_context(context: Dict):
    styles = config.get_style()
    flattened_styles = {}
    utils.flatten_dict(styles, flattened_styles, ["styles"])
    context.update(flattened_styles)
