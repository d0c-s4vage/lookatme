"""
"""


from typing import Dict, Optional

import urwid

from lookatme.widgets.smart_attr_spec import SmartAttrSpec


def _do_get_packed_widget_list(w: urwid.Widget) -> int:
    min_width = 250
    _, orig_rows = w.pack((min_width,))
    curr_rows = orig_rows
    seen = set()
    chunk_size = round(min_width / 2.0)

    last_was_same = True
    while min_width not in seen and min_width > 0:
        _, curr_rows = w.pack((min_width,))
        seen.add(min_width)
        if curr_rows != orig_rows:
            min_width += chunk_size
            if last_was_same and chunk_size == 1:
                break
            last_was_same = False
        else:
            if not last_was_same and chunk_size == 1:
                break
            min_width -= chunk_size
            last_was_same = True
        chunk_size = max(round(chunk_size * 0.5), 1)

    return min_width


def packed_widget_width(w: urwid.Widget) -> int:
    """Return the smallest size of the widget without wrapping"""
    if isinstance(w, urwid.Pile):
        if len(w.widget_list) == 0:
            return 0
        return max(packed_widget_width(x) for x in w.widget_list)
    elif isinstance(w, urwid.Columns):
        res = w.dividechars * (len(w.widget_list) - 1)
        for col_widget, (size_type, size_val, _) in w.contents:
            if size_type == "given":
                res += size_val
            else:
                res += packed_widget_width(col_widget)
        return res
    elif isinstance(w, urwid.AttrMap):
        return packed_widget_width(w.original_widget)
    elif isinstance(w, urwid.Text):
        return max(len(line) for line in w.text.split("\n"))

    return _do_get_packed_widget_list(w)


def debug_print_tokens(tokens, level=1):
    """Print the tokens DFS"""
    import lookatme.config

    def indent(x):
        return "  " * x

    log = lookatme.config.get_log()
    log.debug(indent(level) + "DEBUG TOKENS")
    level += 1

    stack = list(reversed(tokens))
    while len(stack) > 0:
        token = stack.pop()
        if "close" in token["type"]:
            level -= 1

        log.debug(indent(level) + repr(token))

        if "open" in token["type"]:
            level += 1

        token_children = token.get("children", None)
        if isinstance(token_children, list):
            stack.append({"type": "children_close"})
            stack += list(reversed(token_children))
            stack.append({"type": "children_open"})


def check_token_type(token: Optional[Dict], expected_type: str):
    if token is None:
        return
    if token["type"] != expected_type:
        raise Exception(
            "Unexpected token type {!r}, expected {!r}".format(
                token["type"], expected_type
            )
        )


def core_widget(w) -> urwid.Widget:
    """Resolve a wrapped widget to its core widget value"""
    if isinstance(w, urwid.AttrMap):
        return w.base_widget
    return w


def get_meta(item):
    if not hasattr(item, "meta"):
        meta = {}
        setattr(item, "meta", meta)
    else:
        meta = getattr(item, "meta")
    return meta


def prefix_text(text: str, prefix: str, split: str = "\n") -> str:
    return split.join(prefix + part for part in text.split(split))


def row_text(rendered_row):
    """Return all text joined together from the rendered row"""
    return b"".join(x[-1] for x in rendered_row)


def resolve_bag_of_text_markup_or_widgets(items):
    """Resolve the list of items into either contiguous urwid.Text() instances,
    or pre-existing urwid.Widget objects
    """
    res = []
    curr_text_markup = []
    for item in items:
        if isinstance(item, tuple) or isinstance(item, str):
            curr_text_markup.append(item)
        else:
            if len(curr_text_markup) > 0:
                res.append(urwid.Text(curr_text_markup))
                curr_text_markup = []
            res.append(item)

    if len(curr_text_markup) > 0:
        res.append(urwid.Text(curr_text_markup))

    return res


def dict_deep_update(to_update, new_vals):
    """Deeply update the to_update dict with the new_vals"""
    for key, value in new_vals.items():
        if isinstance(value, dict):
            node = to_update.setdefault(key, {})
            dict_deep_update(node, value)
        else:
            to_update[key] = value


def spec_from_style(styles):
    """Create an SmartAttrSpec from a {fg:"", bg:""} style dict. If styles
    is a string, it will be used as the foreground
    """
    if isinstance(styles, str):
        return SmartAttrSpec(styles, "")
    else:
        fg = styles.get("fg", "")
        bg = styles.get("bg", "")
        if fg + bg == "":
            return None
        return SmartAttrSpec(fg, bg)


def non_empty_split(data):
    res = [x.strip() for x in data.split(",")]
    return list(filter(None, res))


def get_fg_bg_styles(style):
    if style is None:
        return [], []

    # from lookatme.config.STYLE
    if isinstance(style, dict):
        return non_empty_split(style["fg"]), non_empty_split(style["bg"])
    # just a str will only set the foreground color
    elif isinstance(style, str):
        return non_empty_split(style), []
    elif isinstance(style, SmartAttrSpec):
        return non_empty_split(style.foreground), non_empty_split(style.background)
    else:
        raise ValueError("Unsupported style value {!r}".format(style))


def extract_hexcolor(spec_style: str) -> str:
    for part in spec_style.split(","):
        if part.startswith("#"):
            return part
    # TODO
    return "#ffffff"


def overwrite_style(
    orig_style: Dict[str, str], new_style: Dict[str, str]
) -> Dict[str, str]:
    orig_spec = spec_from_style(orig_style)
    new_spec = spec_from_style(new_style)
    res_spec = overwrite_spec(orig_spec, new_spec)

    return {
        "fg": res_spec.foreground,
        "bg": res_spec.background,
    }


def overwrite_spec(orig_spec, new_spec):
    if orig_spec is None:
        return new_spec
    if new_spec is None:
        return orig_spec

    import lookatme.widgets.clickable_text

    LinkIndicatorSpec = lookatme.widgets.clickable_text.LinkIndicatorSpec

    if orig_spec is None:
        orig_spec = SmartAttrSpec("", "")
    if new_spec is None:
        new_spec = SmartAttrSpec("", "")

    fg_orig = orig_spec.foreground.split(",")
    fg_orig_color = orig_spec._foreground_color()
    fg_orig.remove(fg_orig_color)

    bg_orig = orig_spec.background.split(",")
    bg_orig_color = orig_spec._background()
    bg_orig.remove(bg_orig_color)

    fg_new = new_spec.foreground.split(",")
    fg_new_color = new_spec._foreground_color()
    fg_new.remove(fg_new_color)

    bg_new = new_spec.background.split(",")
    bg_new_color = new_spec._background()
    bg_new.remove(bg_new_color)

    if fg_new_color in ("", "default"):
        fg_orig.append(fg_orig_color)
    else:
        fg_new.append(fg_new_color)

    if bg_new_color in ("", "default"):
        bg_orig.append(bg_orig_color)
    else:
        bg_new.append(bg_new_color)

    plain_spec = SmartAttrSpec(
        ",".join(set(fg_orig + fg_new)),
        ",".join(set(bg_orig + bg_new)),
    )

    link_spec = None
    if isinstance(orig_spec, LinkIndicatorSpec):
        link_spec = orig_spec
    if isinstance(new_spec, LinkIndicatorSpec):
        link_spec = new_spec

    if link_spec is not None:
        return link_spec.new_for_spec(plain_spec)
    else:
        return plain_spec


def flatten_text(text, new_spec=None):
    """Return a flattend list of tuples that can be used as the first argument
    to a new urwid.Text().

    :param urwid.Text text: The text to flatten
    :param SmartAttrSpec new_spec: A new spec to merge with existing styles
    :returns: list of tuples
    """
    text, chunk_stylings = text.get_text()

    res = []
    total_len = 0
    for spec, chunk_len in chunk_stylings:
        split_text = text[total_len : total_len + chunk_len]
        total_len += chunk_len

        split_text_spec = overwrite_spec(new_spec, spec)
        res.append((split_text_spec, split_text))

    if len(text[total_len:]) > 0:
        res.append((new_spec, text[total_len:]))

    return res


def can_style_item(item):
    """Return true/false if ``style_text`` can work with the given item"""
    return isinstance(item, (urwid.Text, list, tuple))


def _default_filter_fn(_x, _y):
    return True


def spec_from_stack(spec_stack: list, filter_fn=None) -> urwid.AttrSpec:
    if len(spec_stack) == 0:
        return SmartAttrSpec("", "")

    if filter_fn is None:
        filter_fn = _default_filter_fn

    res_spec = SmartAttrSpec("", "")
    for spec, text_only in spec_stack:
        if not filter_fn(spec, text_only):
            continue
        res_spec = overwrite_spec(res_spec, spec)

    return res_spec


def styled_text(text, new_styles, old_styles=None, supplement_style=False):
    """Return a styled text tuple that can be used within urwid.Text.

    .. note::

        If an urwid.Text instance is passed in as the ``text`` parameter,
        alignment values will be lost and must be explicitly re-added by the
        caller.
    """
    if isinstance(text, urwid.Text):
        new_spec = spec_from_style(new_styles)
        return flatten_text(text, new_spec)
    elif (
        isinstance(text, tuple)
        and isinstance(text[0], SmartAttrSpec)
        and isinstance(text[1], urwid.Text)
    ):
        text = text[1].text
        old_styles = text[0]

    new_fg, new_bg = get_fg_bg_styles(new_styles)
    old_fg, old_bg = get_fg_bg_styles(old_styles)

    def join(items):
        return ",".join(set(items))

    spec = SmartAttrSpec(
        join(new_fg + old_fg),
        join(new_bg + old_bg),
    )
    return (spec, text)


def pile_or_listbox_add(container, widgets):
    """Add the widget/widgets to the container"""
    if isinstance(container, urwid.AttrMap):
        container = container.base_widget

    if isinstance(container, urwid.ListBox):
        return listbox_add(container, widgets)
    elif isinstance(container, urwid.Pile):
        return pile_add(container, widgets)
    else:
        raise ValueError("Container was not listbox, nor pile: {!r}".format(container))


def listbox_add(listbox, widgets):
    if not isinstance(widgets, list):
        widgets = [widgets]

    for w in widgets:
        if (
            len(listbox.body) > 0
            and isinstance(w, urwid.Divider)
            and isinstance(listbox.body[-1], urwid.Divider)
        ):
            continue
        listbox.body.append(w)


def pile_add(pile, widgets):
    """ """
    if not isinstance(widgets, list):
        widgets = [widgets]

    for w in widgets:
        if (
            len(pile.contents) > 0
            and isinstance(w, urwid.Divider)
            and isinstance(pile.contents[-1][0], urwid.Divider)
        ):
            continue
        pile.contents.append((w, pile.options()))


def int_to_roman(integer):
    integer = int(integer)
    ints = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    nums = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]
    result = []
    for i in range(len(ints)):
        count = integer // ints[i]
        result.append(nums[i] * count)
        integer -= ints[i] * count
    return "".join(result)
