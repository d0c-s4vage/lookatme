"""
"""


import urwid


def row_text(rendered_row):
    """Return all text joined together from the rendered row
    """
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
    """Deeply update the to_update dict with the new_vals
    """
    for key, value in new_vals.items():
        if isinstance(value, dict):
            node = to_update.setdefault(key, {})
            dict_deep_update(node, value)
        else:
            to_update[key] = value


def spec_from_style(styles):
    """Create an urwid.AttrSpec from a {fg:"", bg:""} style dict. If styles
    is a string, it will be used as the foreground
    """
    if isinstance(styles, str):
        return urwid.AttrSpec(styles, "")
    else:
        return urwid.AttrSpec(styles.get("fg", ""), styles.get("bg", ""))


def get_fg_bg_styles(style):
    if style is None:
        return [], []

    def non_empty_split(data):
        res = [x.strip() for x in data.split(",")]
        return list(filter(None, res))

    # from lookatme.config.STYLE
    if isinstance(style, dict):
        return non_empty_split(style["fg"]), non_empty_split(style["bg"])
    # just a str will only set the foreground color
    elif isinstance(style, str):
        return non_empty_split(style), []
    elif isinstance(style, urwid.AttrSpec):
        return non_empty_split(style.foreground), non_empty_split(style.background)
    else:
        raise ValueError("Unsupported style value {!r}".format(style))


def overwrite_spec(orig_spec, new_spec):
    if orig_spec is None:
        orig_spec = urwid.AttrSpec("", "")
    if new_spec is None:
        new_spec = urwid.AttrSpec("", "")

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

    if fg_new_color == "default":
        fg_orig.append(fg_orig_color)
    else:
        fg_new.append(fg_new_color)

    if bg_new_color == "default":
        bg_orig.append(bg_orig_color)
    else:
        bg_new.append(bg_new_color)

    return urwid.AttrSpec(
        ",".join(set(fg_orig + fg_new)),
        ",".join(set(bg_orig + bg_new)),
    )


def flatten_text(text, new_spec=None):
    """Return a flattend list of tuples that can be used as the first argument
    to a new urwid.Text().

    :param urwid.Text text: The text to flatten
    :param urwid.AttrSpec new_spec: A new spec to merge with existing styles
    :returns: list of tuples
    """
    text, chunk_stylings = text.get_text()

    res = []
    total_len = 0
    for spec, chunk_len in chunk_stylings:
        split_text = text[total_len:total_len + chunk_len]
        total_len += chunk_len

        split_text_spec = overwrite_spec(new_spec, spec)
        res.append((split_text_spec, split_text))

    if len(text[total_len:]) > 0:
        res.append((new_spec, text[total_len:]))

    return res


def can_style_item(item):
    """Return true/false if ``style_text`` can work with the given item
    """
    return isinstance(item, (urwid.Text, list, tuple))


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
    elif (isinstance(text, tuple)
            and isinstance(text[0], urwid.AttrSpec)
            and isinstance(text[1], urwid.Text)):
        text = text[1].text
        old_styles = text[0]

    new_fg, new_bg = get_fg_bg_styles(new_styles)
    old_fg, old_bg = get_fg_bg_styles(old_styles)

    def join(items):
        return ",".join(set(items))

    spec = urwid.AttrSpec(
        join(new_fg + old_fg),
        join(new_bg + old_bg),
    )
    return (spec, text)


def pile_or_listbox_add(container, widgets):
    """Add the widget/widgets to the container
    """
    if isinstance(container, urwid.ListBox):
        return listbox_add(container, widgets)
    elif isinstance(container, urwid.Pile):
        return pile_add(container, widgets)
    else:
        raise ValueError("Container was not listbox, nor pile")


def listbox_add(listbox, widgets):
    if not isinstance(widgets, list):
        widgets = [widgets]

    for w in widgets:
        if len(listbox.body) > 0 \
                and isinstance(w, urwid.Divider) \
                and isinstance(listbox.body[-1], urwid.Divider):
            continue
        listbox.body.append(w)

def pile_add(pile, widgets):
    """
    """
    if not isinstance(widgets, list):
        widgets = [widgets]

    for w in widgets:
        if len(pile.contents) > 0 \
                and isinstance(w, urwid.Divider) \
                and isinstance(pile.contents[-1][0], urwid.Divider):
            continue
        pile.contents.append((w, pile.options()))


# Translate raw_text (ansi sequence) to something readable by urwid (attribut and text)
# from https://github.com/Nanoseb/ncTelegram/blob/29f551ac0e83b1921a6ac697a33fe6eb76ca337a/ncTelegram/ui_msgwidget.py#L335
def translate_color(raw_text):
    formated_text = []
    raw_text = raw_text.decode("utf-8")

    for at in raw_text.split("\x1b["):
        try:
            attr, text = at.split("m",1)
        except:
            attr = '0'
            text = at.split("m",1)

        list_attr = [ int(i) for i in attr.split(';') ]
        list_attr.sort()
        fg = -1
        bg = -1
       
        for elem in list_attr:
            if elem <= 29:
                pass
            elif elem <= 37:
                fg = elem - 30
            elif elem <= 47:
                bg = elem - 40
            elif elem <= 94:
                fg = fg + 8
            elif elem >= 100 and elem <= 104:
                bg = bg + 8
            
        fgcolor = color_list[fg]
        bgcolor = color_list[bg]

        if fg < 0:
            fgcolor = ''
        if bg < 0:
            bgcolor = ''

        if list_attr == [0]:
            fgcolor = ''
            bgcolor = ''

        formated_text.append((urwid.AttrSpec(fgcolor, bgcolor), text))

    return formated_text

def int_to_roman(integer):
    integer = int(integer)
    ints = [1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1]
    nums = ["m",  "cm", "d", "cd","c", "xc","l","xl","x","ix","v","iv","i"]
    result = []
    for i in range(len(ints)):
        count = integer // ints[i]
        result.append(nums[i] * count)
        integer -= ints[i] * count
    return "".join(result)
