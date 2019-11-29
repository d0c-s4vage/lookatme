"""
Defines styles that should look good on dark backgrounds
"""


from collections import defaultdict


code_style = "solarized-dark"
inline_code = None
block_code = None
bullets = {
    "default": "•",
    1: "•",
    2: "⁃",
    3: "◦",
}
table_header_divider = "━"
table_column_spacing = 3

table_alternate_colors = [
    dict(fg="#eee", bg="default"),
    dict(fg="", bg="#222"),
]

quote_style = dict(fg="italics,#aaa", bg="default")
