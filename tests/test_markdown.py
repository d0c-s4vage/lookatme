"""
Test basic markdown renderings
"""


import lookatme.utils as l_utils


import tests.utils as utils
from tests.utils import override_style


@override_style(
    {
        "headings": {
            "default": {
                "fg": "bold",
                "bg": "",
                "prefix": "|",
                "suffix": "|",
            },
        },
    },
    complete=True,
)
def test_heading_defaults(style):
    """Test basic header rendering"""
    utils.validate_render(
        md_text=r"""
            # H1
            ## H2
            ### H3
        """,
        text=[
            "|H1|",
            "    ",
            "|H2|",
            "    ",
            "|H3|",
            "    ",
        ],
        style_mask=[
            "HHHH",
            "////",
            "hhhh",
            "////",
            "aaaa",
            "////",
        ],
        styles={
            "H": style["headings"]["default"],
            "h": style["headings"]["default"],
            "a": style["headings"]["default"],
            "/": {},
        },
    )


@override_style(
    {
        "headings": {
            "default": {
                "fg": "bold",
                "bg": "",
                "prefix": ".",
                "suffix": ".",
            },
            "1": {
                "fg": "bold",
                "bg": "",
                "prefix": "|",
                "suffix": "|",
            },
            "2": {
                "fg": "italics",
                "bg": "",
                "prefix": ">>",
                "suffix": "<<",
            },
            "3": {
                "fg": "underline",
                "bg": "",
                "prefix": "[[[",
                "suffix": "]]]",
            },
        },
    }
)
def test_heading_levels(style):
    """Test basic header rendering"""
    utils.validate_render(
        md_text=r"""
            # H1
            ## H2
            ### H3
        """,
        text=[
            "|H1|    ",
            "        ",
            ">>H2<<  ",
            "        ",
            "[[[H3]]]",
            "        ",
        ],
        style_mask=[
            "HHHH////",
            "////////",
            "hhhhhh//",
            "////////",
            "aaaaaaaa",
            "////////",
        ],
        styles={
            "H": style["headings"]["1"],
            "h": style["headings"]["2"],
            "a": style["headings"]["3"],
            "/": {},
        },
    )


@override_style(
    {
        "table": {
            "column_spacing": 1,
            "header_divider": {"text": "-"},
        }
    }
)
def test_table(style):
    """Test basic table rendering rendering"""
    utils.validate_render(
        render_width=30,
        md_text=r"""
            | H1      |   H2   |     H3 |
            |:--------|:------:|-------:|
            | 1value1 | value2 | value3 |
            | 1       | 2      | 3      |
        """,
        text=[
            "   ┌─────────────────────┐    ",
            "   │H1        H2       H3│    ",
            "   │---------------------│    ",
            "   │1value1 value2 value3│    ",
            "   │1          2        3│    ",
            "   └─────────────────────┘    ",
        ],
        style_mask=[
            "   .......................    ",
            "   .HHHHHHHHHHHHHHHHHHHHH.    ",
            "   .DDDDDDDDDDDDDDDDDDDDD.    ",
            "   .EEEEEEEEEEEEEEEEEEEEE.    ",
            "   .OOOOOOOOOOOOOOOOOOOOO.    ",
            "   .......................    ",
        ],
        styles={
            "H": style["table"]["header"],
            # the divider is part of the header and inherits its styles
            "D": l_utils.overwrite_style(
                style["table"]["header"], style["table"]["header_divider"]
            ),
            "O": style["table"]["odd_rows"],
            "E": style["table"]["even_rows"],
            ".": style["table"]["border"]["tl_corner"],
            " ": {},
        },
    )


@override_style(
    {
        "table": {
            "column_spacing": 1,
            "header_divider": {"text": "-"},
        }
    }
)
def test_table_with_no_body(style):
    """Test table rendering when there isn't a body present"""
    utils.validate_render(
        render_width=10,
        md_text=r"""
            | H1      |   H2   |     H3 |
            |:--------|:------:|-------:|
        """,
        text=[
            "┌────────┐",
            "│H1 H2 H3│",
            "└────────┘",
        ],
        style_mask=[
            "..........",
            ".HHHHHHHH.",
            "..........",
        ],
        styles={
            "H": style["table"]["header"],
            ".": style["table"]["border"]["tl_corner"],
            " ": {},
        },
    )


@override_style(
    {
        "bullets": {
            "default": {"text": "*", "fg": "#505050"},
            "1": {"text": "-", "fg": "#808080"},
            "2": {"text": "=", "fg": "#707070"},
            "3": {"text": "^", "fg": "#606060"},
        },
    },
    complete=True,
)
def test_lists_basic(style):
    """Test list rendering"""
    utils.validate_render(
        md_text=r"""
            * list 1
              * list 2
                * list 3
                  * list 4
              * list 2
                * list 3
                * list 3

            * list 2
        """,
        text=[
            "- list 1      ",
            "  = list 2    ",
            "    ^ list 3  ",
            "      * list 4",
            "  = list 2    ",
            "    ^ list 3  ",
            "    ^ list 3  ",
            "- list 2      ",
        ],
        style_mask=[
            "1             ",
            "  2           ",
            "    3         ",
            "      d       ",
            "  2           ",
            "    3         ",
            "    3         ",
            "1             ",
        ],
        styles={
            "1": style["bullets"]["1"],
            "2": style["bullets"]["2"],
            "3": style["bullets"]["3"],
            "d": style["bullets"]["default"],
            " ": {},
        },
    )


@override_style(
    {
        "bullets": {
            "default": {"text": "*", "fg": "#505050"},
            "1": {"text": "-", "fg": "#808080"},
            "2": {"text": "=", "fg": "#707070"},
            "3": {"text": "^", "fg": "#606060"},
        },
    },
    complete=True,
)
def test_lists_with_newline(style):
    """Test list rendering with a newline between a new nested list and the
    previous list item
    """
    utils.validate_render(
        md_text=r"""
            * list 1

              * list 2
        """,
        text=[
            "- list 1  ",
            "  = list 2",
        ],
        style_mask=[
            "1         ",
            "  2       ",
        ],
        styles={
            "1": style["bullets"]["1"],
            "2": style["bullets"]["2"],
            " ": {},
        },
    )


@override_style(
    {
        "numbering": {
            "default": {"text": "numeric", "fg": "italics"},
            "1": {"text": "numeric", "fg": "italics"},
            "2": {"text": "alpha", "fg": "bold"},
            "3": {"text": "roman", "fg": "underline"},
        },
        "bullets": {
            "default": {"text": "*", "fg": "italics"},
            "3": {"text": "^", "fg": "underline"},
        },
    },
    complete=True,
)
def test_numbered_lists(style):
    """Test list rendering"""
    utils.validate_render(
        md_text=r"""
            1. list 1
                1. alpha1
                1. alpha2
                1. alpha3
            1. list 2
                1. alpha1.1
                    1. roman1
                    1. roman2
                    1. roman3
                1. alpha1.2
                    * test1
                    * test2
            1. list 3
        """,
        text=[
            "1. list 1        ",
            "   a. alpha1     ",
            "   b. alpha2     ",
            "   c. alpha3     ",
            "2. list 2        ",
            "   a. alpha1.1   ",
            "      i. roman1  ",
            "      ii. roman2 ",
            "      iii. roman3",
            "   b. alpha1.2   ",
            "      ^ test1    ",
            "      ^ test2    ",
            "3. list 3        ",
        ],
        style_mask=[
            "11 ______        ",
            "   22 ______     ",
            "   22 ______     ",
            "   22 ______     ",
            "11 ______        ",
            "   22 ________   ",
            "      33 ______  ",
            "      333 ______ ",
            "      3333 ______",
            "   22 ________   ",
            "      B _____    ",
            "      B _____    ",
            "11 ______        ",
        ],
        styles={
            "1": style["numbering"]["1"],
            "2": style["numbering"]["2"],
            "3": style["numbering"]["3"],
            "B": style["bullets"]["3"],
            "_": {},
            " ": {},
        },
    )


@override_style(
    {
        "hrule": {
            "text": "=",
            "fg": "italics",
            "bg": "#004400",
        },
    }
)
def test_hrule(style):
    """Test that hrules render correctly"""
    utils.validate_render(
        render_width=5,
        md_text="""
            ---
        """,
        text=[
            "     ",
            "=====",
            "     ",
        ],
        style_mask=[
            "     ",
            "xxxxx",
            "     ",
        ],
        styles={
            "x": style["hrule"],
            " ": {},
        },
    )


@override_style(
    {
        "quote": {
            "style": {
                "fg": "italics",
                "bg": "#202020",
            },
            "border": {
                "tl_corner": {
                    "text": "██━━──",
                    "fg": "#ff0000",
                },
                "l_line": {
                    "text": "┃",
                    "fg": "#00ff00",
                },
                "bl_corner": {
                    "text": "██━━──",
                    "fg": "#0000ff",
                },
            },
        }
    }
)
def test_block_quote(style):
    """Test block quote rendering"""
    utils.validate_render(
        md_text="""
            > Quote text
            >
            > Quote italic text
            >
            > Quote text
        """,
        text=[
            "██━━──               ",
            "┃  Quote text        ",
            "┃                    ",
            "┃  Quote italic text ",
            "┃                    ",
            "┃  Quote text        ",
            "██━━──               ",
        ],
        style_mask=[
            "TTTTTT_______________",
            "Liiiiiiiiiiiiiiiiiii_",
            "Liiiiiiiiiiiiiiiiiii_",
            "Liiiiiiiiiiiiiiiiiii_",
            "Liiiiiiiiiiiiiiiiiii_",
            "Liiiiiiiiiiiiiiiiiii_",
            "BBBBBB_______________",
        ],
        styles={
            "T": style["quote"]["border"]["tl_corner"],
            "L": style["quote"]["border"]["l_line"],
            "B": style["quote"]["border"]["bl_corner"],
            "i": style["quote"]["style"],
            "_": {},
            " ": {},
        },
    )


@override_style(
    {
        "code": "monokai",
    }
)
def test_code(styles):
    """Test code block rendering"""
    utils.validate_render(
        md_text="""
            ```python
            'Hello'
            'Hello'
            'Hello'
            'Hello'
            ```
        """,
        text=[
            "       ",
            "'Hello'",
            "'Hello'",
            "'Hello'",
            "'Hello'",
            "       ",
        ],
        style_mask=[
            "       ",
            "RRRRRRR",
            "RRRRRRR",
            "RRRRRRR",
            "RRRRRRR",
            "       ",
        ],
        styles={
            "R": {"fg": "#dd8", "bg": "g15"},
            " ": {},
        },
    )


@override_style(
    {
        "code": "monokai",
    }
)
def test_empty_codeblock(style):
    """Test that empty code blocks render correctly"""
    utils.validate_render(
        md_text="""
            ```python

            ```
        """,
        text=[
            " ",
            " ",
            " ",
        ],
        style_mask=[
            " ",
            "B",
            " ",
        ],
        styles={
            "B": {"bg": "g15"},
            " ": {},
        },
    )


@override_style(
    {
        "code": "monokai",
    }
)
def test_code_yaml(styles):
    """Test code block rendering with yaml language"""
    utils.validate_render(
        md_text="""
            ```yaml
            test: a value
            test2: "another value"
            array:
              - item1
              - item2
              - item3
            ```
        """,
        text=[
            "                      ",
            "test: a value         ",
            'test2: "another value"',
            "array:                ",
            "  - item1             ",
            "  - item2             ",
            "  - item3             ",
            "                      ",
        ],
        style_mask=[
            "                      ",
            "KKKK::VVVVVVV_________",
            "KKKKK::SSSSSSSS:SSSSSS",
            "KKKKK:________________",
            "::::VVVVV_____________",
            "::::VVVVV_____________",
            "::::VVVVV_____________",
            "                      ",
        ],
        styles={
            "K": {"fg": "#f06", "bg": "g15"},
            "S": {"fg": "#dd8", "bg": "g15"},
            "V": {"fg": "#a8f", "bg": "g15"},
            ":": {"fg": "g93", "bg": "g15"},
            "-": {"bg": "g15"},
            "_": {"bg": "g15"},
            " ": {},
        },
    )


@override_style(
    {
        "link": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_link(styles):
    utils.validate_render(
        md_text="""
            [text](href)
        """,
        text=[
            "text",
        ],
        style_mask=[
            "TTTT",
        ],
        styles={
            "T": styles["link"],
        },
    )


@override_style(
    {
        "emphasis": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_emphasis(styles):
    utils.validate_render(
        md_text="""
            *emphasis*

            _emphasis_
        """,
        text=[
            "emphasis",
            "        ",
            "emphasis",
        ],
        style_mask=[
            "EEEEEEEE",
            "        ",
            "EEEEEEEE",
        ],
        styles={
            "E": styles["emphasis"],
            " ": {},
        },
    )


@override_style(
    {
        "strong_emphasis": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_strong_emphasis(styles):
    utils.validate_render(
        md_text="""
            **strong emphasis**

            __strong emphasis__
        """,
        text=[
            "strong emphasis",
            "               ",
            "strong emphasis",
        ],
        style_mask=[
            "EEEEEEEEEEEEEEE",
            "               ",
            "EEEEEEEEEEEEEEE",
        ],
        styles={
            "E": styles["strong_emphasis"],
            " ": {},
        },
    )


@override_style(
    {
        "emphasis": {
            "fg": "italics",
            "bg": "default",
        },
        "strong_emphasis": {
            "fg": "bold",
            "bg": "#00ff00",
        },
    }
)
def test_emphasis_strong_emphasis(styles):
    utils.validate_render(
        md_text="""
            *em **strong emphasis** em*

            ***strong emphasis***

            _em __strong emphasis__ em_

            ___strong emphasis___
        """,
        text=[
            "em strong emphasis em",
            "                     ",
            "strong emphasis      ",
            "                     ",
            "em strong emphasis em",
            "                     ",
            "strong emphasis      ",
        ],
        style_mask=[
            "EEEDDDDDDDDDDDDDDDEEE",
            "                     ",
            "DDDDDDDDDDDDDDD      ",
            "                     ",
            "EEEDDDDDDDDDDDDDDDEEE",
            "                     ",
            "DDDDDDDDDDDDDDD      ",
        ],
        styles={
            "E": styles["emphasis"],
            # both emphasis and strong_emphasis styles
            "D": {"fg": "italics,bold", "bg": "#00ff00"},
            " ": {},
        },
    )


@override_style(
    {
        "strikethrough": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_strikethrough(styles):
    utils.validate_render(
        md_text="""
            ~~strikethrough~~
        """,
        text=[
            "strikethrough",
        ],
        style_mask=[
            "SSSSSSSSSSSSS",
        ],
        styles={
            "S": styles["strikethrough"],
        },
    )


@override_style(
    {
        "link": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_plain_url(styles):
    utils.validate_render(
        md_text="""
            https://github.com/d0c-s4vage/lookatme
        """,
        text=[
            "https://github.com/d0c-s4vage/lookatme",
        ],
        style_mask=[
            "LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL",
        ],
        styles={
            "L": styles["link"],
        },
    )


@override_style(
    {
        "link": {
            "fg": "#ff0000",
            "bg": "#00ff00",
        }
    }
)
def test_image_as_link(styles):
    utils.validate_render(
        md_text="""
            ![link_text](image_url)
        """,
        text=[
            "link_text",
        ],
        style_mask=[
            "LLLLLLLLL",
        ],
        styles={
            "L": styles["link"],
        },
    )


def test_softbreak():
    utils.validate_render(
        md_text="""
            hello
            world
        """,
        text=[
            "hello world",
        ],
        style_mask=[
            "XXXXXXXXXXX",
        ],
        styles={
            "X": {},
        },
    )


def test_softbreak_with_dash():
    utils.validate_render(
        md_text="""
            hello-
            world
            hello world
            hello world
        """,
        text=[
            "hello-world hello world hello world",
        ],
        style_mask=[
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ],
        styles={
            "X": {},
        },
    )
