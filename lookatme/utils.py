"""
"""


import urwid


def dict_deep_update(to_update, new_vals):
    """Deeply update the to_update dict with the new_vals
    """
    for key, value in new_vals.items():
        if isinstance(value, dict):
            node = to_update.setdefault(key, {})
            dict_deep_update(node, value)
        else:
            to_update[key] = value


def spec_from_style(style_dict):
    """Create an urwid.AttrSpec from a {fg:"", bg:""} style dict
    """
    return urwid.AttrSpec(style_dict.get("fg", ""), style_dict.get("bg", ""))


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


def styled_text(text, new_styles, old_styles=None):
    """Return a styled text tuple that can be used within urwid.Text.

    .. note::

        If an urwid.Text instance is passed in as the ``text`` parameter,
        alignment values will be lost and must be explicitly re-added by the
        caller.
    """
    if isinstance(text, urwid.Text):
        text = text.text
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
