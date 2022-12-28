"""
This module renders lookatme slides to HTML
"""


from collections import deque, OrderedDict
from contextlib import contextmanager
import glob
import inspect
import os
import shutil
from typing import Any, Dict, List, Optional, OrderedDict, Tuple


import urwid


import lookatme.config as config
from lookatme.widgets.clickable_text import LinkIndicatorSpec
import lookatme.render.html.templating as templating


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
    def use_spec(self, spec: Optional[urwid.AttrSpec]):
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

        if isinstance(spec, LinkIndicatorSpec):
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
    return (
        text.replace("&", "&amp;")
        .replace(" ", "&nbsp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _keep_text(text_idx: int, text: str, keep_range: range) -> str:
    text_stop = text_idx + len(text)

    if text_stop < keep_range.start:
        return ""

    if text_idx > keep_range.stop:
        return ""

    start = max(keep_range.start, text_idx)
    stop = min(text_stop, keep_range.stop)

    return text[start - text_idx : stop - text_idx]


def canvas_to_html(
    ctx: HtmlContext, canvas: urwid.Canvas, only_keep: Optional[str] = None
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

            if text == "":
                continue

            with ctx.use_spec(spec):
                ctx.write(text)

        if idx != len(canvas.text) - 1:
            ctx.write("<br/>\n")


def _create_slide_nav(
    titles: List[Tuple[str, Optional[urwid.Canvas]]],
    category_delim: Optional[str] = None,
) -> str:
    nav: OrderedDict[str, Any] = OrderedDict()
    nav["__children__"] = OrderedDict()

    for slide_idx, (title_text, title_canvas) in enumerate(titles):
        if category_delim is not None:
            categories = [x.strip() for x in title_text.split(category_delim)]
        else:
            categories = [title_text]

        curr_nav = nav
        for idx, category in enumerate(categories):
            if title_canvas is None:
                html_title = "<span>" + title_text + "</span>"
            else:
                ctx = HtmlContext()
                canvas_to_html(ctx, title_canvas, only_keep=category)
                html_title = ctx.get_html().strip()

            children = curr_nav.setdefault("__children__", OrderedDict())
            cat_info = children.get(category, None)  # type: ignore
            if not cat_info:
                cat_info = children[category] = OrderedDict(
                    {"__slide__": None, "__html__": html_title}
                )

            # only keep the first slide (main use case here is progressive
            # slides that all have the same title)
            if idx == len(categories) - 1 and not cat_info["__slide__"]:
                cat_info["__slide__"] = slide_idx  # type: ignore
            else:
                curr_nav = cat_info

    ctx = HtmlContext()
    _render_nav_tree(ctx, nav)
    return ctx.get_html()


def _create_slide_deck(slides_html: List[Tuple[str, str, str]]) -> str:
    ctx = HtmlContext()
    for slide_idx, (header_html, body_html, footer_html) in enumerate(slides_html):
        with ctx.use_tag("div", classname="slide", **{"data-slide-idx": slide_idx}):
            with ctx.use_tag("div", classname="slide-header"):
                ctx.write(header_html)
            with ctx.use_tag("div", classname="slide-body"):
                with ctx.use_tag("div", classname="slide-body-inner", tabindex=-1):
                    with ctx.use_tag("div", classname="slide-body-inner-inner"):
                        ctx.write(body_html)
            with ctx.use_tag("div", classname="slide-footer"):
                ctx.write(footer_html)

    return ctx.get_html()


def _flatten_dict(tree_dict: Dict, flat_dict: Dict, prefixes: Optional[List] = None):
    prefixes = prefixes or []
    for k, v in tree_dict.items():
        if isinstance(v, dict):
            _flatten_dict(v, flat_dict, prefixes + [k])
            continue
        flat_k = ".".join(prefixes + [k])
        flat_dict[flat_k] = v


def _add_styles_to_context(context: Dict):
    styles = config.get_style()
    flattened_styles = {}
    _flatten_dict(styles, flattened_styles, ["styles"])
    context.update(flattened_styles)


def copy_tree_update(src: str, dst: str):
    """Copy a directory from src to dst. For each directory within src,
    ensure that the directory exists, and then copy each individual file in.
    If other files exist in that same directory in dst, leave them alone.
    """
    if not os.path.exists(dst):
        shutil.copytree(src, dst)
        return

    for src_subpath in glob.glob(os.path.join(src, "*")):
        relpath = os.path.relpath(src_subpath, src)
        dst_subpath = os.path.join(dst, relpath)

        if os.path.isfile(src_subpath):
            shutil.copy(src_subpath, dst_subpath)
        elif os.path.isdir(src_subpath):
            copy_tree_update(src_subpath, dst_subpath)


def create_html_output(
    output_dir: str,
    slides_html: List[Tuple[str, str, str]],
    slides_titles: List[Tuple[str, Optional[urwid.Canvas]]],
    title_category_delim: str = ":",
):
    slide_deck = _create_slide_deck(slides_html)
    slide_nav = _create_slide_nav(slides_titles, title_category_delim)

    context = {}
    _add_styles_to_context(context)
    script = templating.render("script.template.js", context)
    styles = templating.render("styles.template.css", context)

    context.update(
        {
            "styles": styles,
            "script": script,
            "nav": slide_nav,
            "slide_deck": slide_deck,
        }
    )
    single_page_html = templating.render("single_page.template.html", context)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    dst_static_dir = os.path.join(output_dir, "static")
    copy_tree_update(static_dir, dst_static_dir)

    index_html_path = os.path.join(output_dir, "index.html")
    with open(index_html_path, "w") as f:
        f.write(single_page_html)


def _render_nav_tree(ctx: HtmlContext, tree: OrderedDict):
    with ctx.use_tag("ul"):
        for _, info in tree["__children__"].items():
            classname = "navitem"
            html_title = info["__html__"]
            attrs = {}

            if info["__slide__"] is not None:
                attrs["data-slide-idx"] = info["__slide__"]
                classname += " navitem-slide"

            with ctx.use_tag("li", classname=classname, **attrs):
                ctx.write(html_title)

            if "__children__" in info:
                _render_nav_tree(ctx, info)
