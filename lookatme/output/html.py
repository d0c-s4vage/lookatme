"""
Output an entire slide deck into an interactive html file
"""


from collections import OrderedDict
import os
from typing import Any, Tuple, List, Optional


import urwid


from lookatme.output.base import BaseOutputFormat
from lookatme.pres import Presentation
import lookatme.render.html as html
import lookatme.utils.fs as fs_utils
from lookatme.tutorial import tutor


class HtmlSlideDeckOutputFormat(BaseOutputFormat):
    NAME = "html"
    DEFAULT_OPTIONS = {
        "cols": 100,
        "rows": 30,
        "title_delim": ":",
        "render_images": True,
    }

    def do_format_pres(self, pres: Presentation, output_path: str):
        """ """
        slides_html, slides_titles = self._create_html(
            pres=pres,
            width=self.opt("cols"),
            render_images=self.opt("render_images"),
        )

        self._create_html_output(
            output_dir=output_path,
            slides_html=slides_html,
            slides_titles=slides_titles,
            title_category_delim=self.opt("title_delim"),
        )

    def _create_html(
        self,
        pres: Presentation,
        width: int = 150,
        render_images: bool = True,
    ) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, Optional[urwid.Canvas]]]]:
        pres.tui_init_sync()
        ctx = html.HtmlContext()

        if pres.tui is None:
            raise RuntimeError()

        # header, body, footer contents, not wrapped in divs with classes
        # yet
        raw_slides_html: List[Tuple[str, str, str]] = []
        titles: List[Tuple[str, Optional[urwid.Canvas]]] = []
        for slide_idx, slide in enumerate(pres.slides):
            titles.append(slide.get_title(pres.tui.ctx))
            pres.tui.set_slide_idx(slide_idx)

            header, body, footer = pres.tui.render_without_scrollbar(width)
            classname = "slide"
            if slide_idx != 0:
                classname += " hidden"

            html.canvas_to_html(ctx, header, render_images=render_images)
            header_html = ctx.get_html_consumed()

            html.canvas_to_html(ctx, body, render_images=render_images)
            body_html = ctx.get_html_consumed()

            html.canvas_to_html(ctx, footer, render_images=render_images)
            footer_html = ctx.get_html_consumed()

            raw_slides_html.append((header_html, body_html, footer_html))

        return raw_slides_html, titles

    def _create_slide_nav(
        self,
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
                    ctx = html.HtmlContext()
                    html.canvas_to_html(ctx, title_canvas, only_keep=category)
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

        ctx = html.HtmlContext()
        self._render_nav_tree(ctx, nav)
        return ctx.get_html()

    def _create_slide_deck(self, slides_html: List[Tuple[str, str, str]]) -> str:
        ctx = html.HtmlContext()
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

    def _create_html_output(
        self,
        output_dir: str,
        slides_html: List[Tuple[str, str, str]],
        slides_titles: List[Tuple[str, Optional[urwid.Canvas]]],
        title_category_delim: str = ":",
    ):
        slide_deck = self._create_slide_deck(slides_html)
        slide_nav = self._create_slide_nav(slides_titles, title_category_delim)

        context = {}
        html.add_styles_to_context(context)
        script = self.render_template("script.template.js", context)
        styles = self.render_template("styles.template.css", context)

        context.update(
            {
                "styles": styles,
                "script": script,
                "nav": slide_nav,
                "slide_deck": slide_deck,
            }
        )
        single_page_html = self.render_template("single_page.template.html", context)

        static_dir = os.path.join(os.path.dirname(__file__), "html_static")
        dst_static_dir = os.path.join(output_dir, "static")
        fs_utils.copy_tree_update(static_dir, dst_static_dir)

        index_html_path = os.path.join(output_dir, "index.html")
        with open(index_html_path, "w") as f:
            f.write(single_page_html)

    def _render_nav_tree(self, ctx: html.HtmlContext, tree: OrderedDict):
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
                    self._render_nav_tree(ctx, info)
