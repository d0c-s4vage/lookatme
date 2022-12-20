"""
Test slide rendering
"""

import yaml


import tests.utils as utils
from tests.utils import override_style


@override_style(
    {
        "slides": {
            "fg": "#ff0000",
            "bg": "#00ffff",
        },
        "title": {
            "fg": "#111100",
            "bg": "#001111",
        },
        "slide_number": {
            "fg": "#222200",
            "bg": "#002222",
        },
        "author": {
            "fg": "#333300",
            "bg": "#003333",
        },
        "date": {
            "fg": "#444400",
            "bg": "#004444",
        },
        "margin": {
            "top": 0,
            "bottom": 0,
            "left": 0,
            "right": 0,
        },
        "padding": {
            "top": 0,
            "bottom": 0,
            "left": 0,
            "right": 0,
        },
    },
    complete=True,
)
def test_basic_slide(style):
    """Test that styles are applied correctly to the different slide elements"""
    meta = {
        "title": "title",
        "styles": style,
        "date": "DATE",
        "author": "me",
    }
    md = r"""
---
{}
---
Hello world
    """.format(
        yaml.dump(meta)
    )

    utils.validate_render(
        as_slide=True,
        render_width=30,
        render_height=4,
        md_text=md,
        text=[
            "             title            ",
            "Hello world                   ",
            "                              ",
            "me DATE            slide 1 / 1",
        ],
        style_mask=[
            "_____________TTTTT____________",
            "sssssssssss___________________",
            "______________________________",
            "AA_DDDD____________SSSSSSSSSSS",
        ],
        styles={
            "T": style["title"],
            "s": style["slides"],
            "A": style["author"],
            "D": style["date"],
            "S": style["slide_number"],
            "_": style["slides"],
        },
    )


@override_style(
    {
        "slides": {
            "fg": "#ff0000",
            "bg": "#00ffff",
        },
        "title": {
            "fg": "#111100",
            "bg": "#001111",
        },
        "slide_number": {
            "fg": "#222200",
            "bg": "#002222",
        },
        "author": {
            "fg": "#333300",
            "bg": "#003333",
        },
        "date": {
            "fg": "#444400",
            "bg": "#004444",
        },
        "margin": {
            "top": 1,
            "bottom": 1,
            "left": 1,
            "right": 1,
        },
        "padding": {
            "top": 0,
            "bottom": 0,
            "left": 0,
            "right": 0,
        },
    },
    complete=True,
)
def test_slide_margin(style):
    """Test that styles are applied correctly to the different slide elements"""
    meta = {
        "title": "title",
        "styles": style,
        "date": "DATE",
        "author": "me",
    }
    md = r"""
---
{}
---
Hello world
    """.format(
        yaml.dump(meta)
    )

    utils.validate_render(
        as_slide=True,
        render_width=30,
        render_height=6,
        md_text=md,
        text=[
            "                              ",
            "             title            ",
            " Hello world                  ",
            "                              ",
            " me DATE          slide 1 / 1 ",
            "                              ",
        ],
        style_mask=[
            "______________________________",
            "_____________TTTTT____________",
            "_sssssssssss__________________",
            "______________________________",
            "_AA_DDDD__________SSSSSSSSSSS_",
            "______________________________",
        ],
        styles={
            "T": style["title"],
            "s": style["slides"],
            "A": style["author"],
            "D": style["date"],
            "S": style["slide_number"],
            "_": style["slides"],
        },
    )


@override_style(
    {
        "slides": {
            "fg": "#ff0000",
            "bg": "#00ffff",
        },
        "title": {
            "fg": "#111100",
            "bg": "#001111",
        },
        "slide_number": {
            "fg": "#222200",
            "bg": "#002222",
        },
        "author": {
            "fg": "#333300",
            "bg": "#003333",
        },
        "date": {
            "fg": "#444400",
            "bg": "#004444",
        },
        "margin": {
            "top": 0,
            "bottom": 0,
            "left": 0,
            "right": 0,
        },
        "padding": {
            "top": 1,
            "bottom": 1,
            "left": 1,
            "right": 1,
        },
    },
    complete=True,
)
def test_slide_padding(style):
    """Test that styles are applied correctly to the different slide elements"""
    meta = {
        "title": "title",
        "styles": style,
        "date": "DATE",
        "author": "me",
    }
    md = r"""
---
{}
---
Hello world
    """.format(
        yaml.dump(meta)
    )

    utils.validate_render(
        as_slide=True,
        render_width=30,
        render_height=5,
        md_text=md,
        text=[
            "             title            ",
            "                              ",
            " Hello world                  ",
            "                              ",
            "me DATE            slide 1 / 1",
        ],
        style_mask=[
            "_____________TTTTT____________",
            "______________________________",
            "__sssssssssss_________________",
            "______________________________",
            "AA_DDDD____________SSSSSSSSSSS",
        ],
        styles={
            "T": style["title"],
            "s": style["slides"],
            "A": style["author"],
            "D": style["date"],
            "S": style["slide_number"],
            "_": style["slides"],
        },
    )


@override_style(
    {
        "slides": {
            "fg": "#ff0000",
            "bg": "#00ffff",
        },
        "title": {
            "fg": "#111100",
            "bg": "#001111",
        },
        "slide_number": {
            "fg": "#222200",
            "bg": "#002222",
        },
        "author": {
            "fg": "#333300",
            "bg": "#003333",
        },
        "date": {
            "fg": "#444400",
            "bg": "#004444",
        },
        "margin": {
            "top": 0,
            "bottom": 0,
            "left": 0,
            "right": 0,
        },
        "padding": {
            "top": 1,
            "bottom": 1,
            "left": 1,
            "right": 1,
        },
        "scrollbar": {
            "slider": {
                "top_chars": ["*", "X"],
                "fill": "X",
                "bottom_chars": ["*", "X"],
                "fg": "#334455",
                "bg": "#534453",
            },
            "gutter": {
                "fill": "-",
                "fg": "#994455",
                "bg": "#594459",
            },
        },
    },
    complete=True,
)
def test_slide_scrollbar(style):
    """Test that styles are applied correctly to the different slide elements"""
    meta = {
        "title": "title",
        "styles": style,
        "date": "DATE",
        "author": "me",
    }
    md = r"""
---
{}
---
Hi\
Hi\
Hi\
Hi\
Hi\
Hi\
Hi\
Hi\
    """.format(
        yaml.dump(meta)
    )

    utils.validate_render(
        as_slide=True,
        render_width=30,
        render_height=9,  # should be four lines not in view
        md_text=md,
        text=[
            "             title            ",
            "                              ",
            " Hi                          X",
            " Hi                          X",
            " Hi                          X",
            " Hi                          *",
            " Hi                          -",
            "                              ",
            "me DATE            slide 1 / 1",
        ],
        style_mask=[
            "_____________TTTTT____________",
            "______________________________",
            "__ss_________________________L",
            "__ss_________________________L",
            "__ss_________________________L",
            "__ss_________________________L",
            "__ss_________________________G",
            "______________________________",
            "AA_DDDD____________SSSSSSSSSSS",
        ],
        styles={
            "T": style["title"],
            "s": style["slides"],
            "A": style["author"],
            "D": style["date"],
            "S": style["slide_number"],
            "_": style["slides"],
            "L": style["scrollbar"]["slider"],
            "G": style["scrollbar"]["gutter"],
        },
    )
