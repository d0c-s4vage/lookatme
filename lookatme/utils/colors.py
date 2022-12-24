"""
Color-related utilities
"""


import math
import re


import urwid


import lookatme.utils as utils


def ensure_contrast(spec: urwid.AttrSpec):
    luminance_fg = luminance(utils.extract_hexcolor(spec.foreground))
    luminance_bg = luminance(utils.extract_hexcolor(spec.background))

    if luminance_fg > luminance_bg:
        contrast_ratio = (luminance_fg + 0.05) / (luminance_bg + 0.05)
    else:
        contrast_ratio = (luminance_bg + 0.05) / (luminance_fg + 0.05)

    # w3c recommends a contrast >= 4.5, but most coding color schemes don't
    # fit this
    if contrast_ratio >= 3.0:
        return

    if luminance_bg < 0.5:
        new_fg = "#ffffff"
    else:
        new_fg = "#000000"

    tmp_spec = utils.overwrite_style(
        {"fg": spec.foreground},
        {"fg": new_fg},
    )
    spec.foreground = tmp_spec["fg"]


def luminance(color: str) -> float:
    color = color.strip("#")
    if len(color) != 6:
        return 0.0

    red, green, blue = [int(x, 16) for x in re.findall("..", color)]
    red = math.pow(red / 255.0, 2.2)
    green = math.pow(green / 255.0, 2.2)
    blue = math.pow(blue / 255.0, 2.2)

    return red * 0.2126 + green * 0.7152 + blue * 0.0722


def increase_brightness(color: str, percent: float) -> str:
    color = color.strip("#")
    red, green, blue = [int(x, 16) for x in re.findall("..", color)]

    if percent > 0:
        red += (255.0 - red) * percent
        green += (255.0 - green) * percent
        blue += (255.0 - blue) * percent
    else:
        red += red * percent
        green += green * percent
        blue += blue * percent

    if percent < 0:
        red = max(0, red)
        green = max(0, green)
        blue = max(0, blue)
    else:
        red = min(255, red)
        green = min(255, green)
        blue = min(255, blue)

    return "#{:02x}{:02x}{:02x}".format(int(red), int(green), int(blue))


def get_highlight_color(bg_color: str, percent: float = 0.1) -> str:
    bg_luminance = luminance(bg_color)
    if bg_luminance > 0.5:
        hl_color = increase_brightness(bg_color, -percent)
    else:
        hl_color = increase_brightness(bg_color, percent)

    return hl_color
