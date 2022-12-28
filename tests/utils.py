"""
Defines utilities for testing lookatme
"""


from functools import wraps
import inspect
from six.moves import StringIO  # type: ignore
from typing import cast, Any, Dict, List, Optional, Tuple, Union
import urwid

from lookatme.render.context import Context
import lookatme.config
import lookatme.schemas
import lookatme.parser
import lookatme.utils as utils
import lookatme.render.markdown_block as markdown_block
from lookatme.pres import Presentation
import lookatme.tui


def to_vtext(fg_bg: Tuple[str, str], texts: List[str]) -> str:
    text = "".join(texts)
    if text == "":
        return ""

    fg, bg = fg_bg

    fg = ",".join(sorted(filter(lambda x: x != "default", fg.split(","))))
    bg = ",".join(sorted(filter(lambda x: x != "default", bg.split(","))))

    parts = []
    if fg != "":
        parts.append("fg:" + fg)

    if bg != "":
        parts.append("bg:" + bg)

    return "<{}>{}</>".format(" ".join(parts), text)


def _markups_to_vtext(
    items: List[Tuple[Union[None, urwid.AttrSpec], Any, bytes]]
) -> str:
    res = []
    tag_stack: List[Tuple[Tuple[str, str], List[str]]] = [(("default", "default"), [])]
    for item in items:
        spec, text = spec_and_text(item)
        text = text.decode()

        if spec is None:
            fg = "default"
            bg = "default"
        else:
            fg = spec.foreground
            bg = spec.background

        if fg == "":
            fg = "default"
        if bg == "":
            bg = "default"

        if tag_stack[-1][0] == (fg, bg):
            tag_stack[-1][1].append(text)
            continue

        res.append(tag_stack.pop())
        tag_stack.append(((fg, bg), [text]))

    res.append(tag_stack.pop())
    res_text = []
    for vtext_info in res:
        res_text.append(to_vtext(*vtext_info))

    return "".join(res_text)


def validate_row(markup_row, v_expected):
    v_actual = _markups_to_vtext(markup_row)
    print(v_actual)
    print(v_expected)
    assert v_actual == v_expected


def _vtext_from_text_and_style(text: str, style: Dict[str, str]) -> str:
    fg = style.get("fg", "")
    bg = style.get("bg", "")
    return to_vtext((fg, bg), [text])


def _vtext_from_text_and_style_mask(
    text: str, style_mask: str, styles: Dict[str, Dict[str, str]]
) -> str:
    curr_text = ""
    curr_style = {}
    res = []
    for idx in range(len(text)):
        mask = style_mask[idx]
        style = styles[mask]
        char = text[idx]
        if style != curr_style and curr_text != "":
            res.append(_vtext_from_text_and_style(curr_text, curr_style))
            curr_text = ""
        curr_style = style
        curr_text += char

    res.append(_vtext_from_text_and_style(curr_text, curr_style))
    return "".join(res)


def render_widget(
    w: urwid.Widget, width: Optional[int] = None
) -> List[List[Tuple[Optional[urwid.AttrSpec], Any, bytes]]]:
    if width is None:
        width = utils.packed_widget_width(w)

    return list(w.render((width,), False).content())


def render_md(
    md_text: str, width: Optional[int] = None
) -> List[List[Tuple[Optional[urwid.AttrSpec], Any, bytes]]]:
    tokens = lookatme.parser.md_to_tokens(md_text)

    root = urwid.Pile([])
    ctx = Context(None)
    ctx.clean_state_snapshot()

    with ctx.use_tokens(tokens):
        with ctx.use_container(root, is_new_block=True):
            markdown_block.render_all(ctx, and_unwind=True)

    ctx.clean_state_validate()

    return render_widget(root, width)


def validate_render(
    text: List[str],
    style_mask: List[str],
    styles: Dict[str, Dict[str, str]],
    md_text: Optional[str] = None,
    rendered: Optional[List[List[Tuple[Optional[urwid.AttrSpec], Any, bytes]]]] = None,
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    as_slide: Optional[bool] = False,
):
    """render_height is only used when as_slide=True"""
    if md_text is not None:
        md_text = inspect.cleandoc(md_text)
        if as_slide:
            assert render_width is not None
            assert render_height is not None
            input_stream = StringIO(md_text)
            pres = Presentation(input_stream, "dark")
            tui = lookatme.tui.create_tui(pres)
            tui.slide_renderer.stop()
            tui.slide_renderer.join()
            loop_widget = tui.loop.widget
            canvas = loop_widget.render((render_width, render_height), False)
            rendered = list(canvas.content())
        else:
            rendered = render_md(md_text, width=render_width)

    if rendered is None:
        raise Exception("Rendered should not be none here")

    # should have the same number of rows
    assert len(rendered) == len(
        text
    ), "Rendered and expected don't have same # rows: {} rendered, {} expected".format(
        len(rendered), len(text)
    )

    assert len(text) == len(style_mask)
    for idx in range(len(text)):
        assert len(text[idx]) == len(
            style_mask[idx]
        ), "Text length doesn't match style mask length"

        row_vtext = _vtext_from_text_and_style_mask(text[idx], style_mask[idx], styles)
        rendered_vtext = _markups_to_vtext(rendered[idx])
        assert row_vtext == rendered_vtext, f"Row idx {idx} did not match"


def setup_lookatme(tmpdir, mocker, style=None):
    mocker.patch.object(lookatme.config, "LOG")
    mocker.patch("lookatme.config.SLIDE_SOURCE_DIR", new=str(tmpdir))

    if style is not None:
        mocker.patch("lookatme.config.STYLE", new=style)


def precise_update(full_style, new_style):
    for k, v in new_style.items():
        if isinstance(v, dict):
            if k in full_style and isinstance(full_style[k], dict):
                precise_update(full_style[k], v)
        else:
            full_style[k] = v


def create_style(new_style: Dict, complete: bool = False):
    full_style = cast(Dict, lookatme.schemas.StyleSchema().dump(None))
    if complete:
        full_style.update(new_style)
    else:
        precise_update(full_style, new_style)
    return full_style


def override_style(new_style: Dict, complete=False, pass_tmpdir=False):
    """Override the style settings for lookatme. By default a precise update
    will be performed where nested subkeys will be specifically updated if
    they exist in the original style dict.

    If ``complete`` is ``True``, then a normal dict.update() is used which
    overrides entire trees in the style dict.
    """

    def outer(fn):
        full_style = create_style(new_style, complete)
        fn.style = full_style

        def inner(tmpdir, mocker):
            setup_lookatme(tmpdir, mocker, style=full_style)
            if pass_tmpdir:
                return fn(tmpdir, full_style)
            else:
                return fn(full_style)

        return inner

    return outer


def assert_render(correct_render, rendered, full_strip=False):
    for idx, row in enumerate(rendered):
        if full_strip:
            stripped = row_text(row).strip()
        else:
            stripped = row_text(row).rstrip()
        if idx >= len(correct_render):
            assert stripped == b""
        else:
            assert correct_render[idx] == stripped


def spec_and_text(item):
    """``item`` should be an item from a rendered widget, a tuple of the form

    .. code-block:: python

        (spec, ?, text)
    """
    return item[0], item[2]


def row_text(rendered_row):
    """Return all text joined together from the rendered row"""
    return b"".join(x[-1] for x in rendered_row)
