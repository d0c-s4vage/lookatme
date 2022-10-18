"""
Test basic markdown renderings
"""


from lookatme.schemas import StyleSchema
import lookatme.utils as l_utils


import tests.utils as utils
from tests.utils import override_style


@override_style({
    "headings": {
        "default": {
            "fg": "bold",
            "bg": "",
            "prefix": "|",
            "suffix": "|",
        },
    },
}, complete=True)
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
        }
    )


@override_style({
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
})
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
        }
    )


@override_style({
    "table": {
        "column_spacing": 1,
        "header_divider": { "text": "-" },
    }
})
def test_table(style):
    """Test basic header rendering"""
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
                style["table"]["header"],
                style["table"]["header_divider"]
            ),
            "O": style["table"]["odd_rows"],
            "E": style["table"]["even_rows"],
            ".": style["table"]["border"]["tl_corner"],
            " ": {},
        }
    )


@override_style({
    "bullets": {
        "default": { "text": "*", "fg": "#505050" },
        "1": { "text": "-", "fg": "#808080" },
        "2": { "text": "=", "fg": "#707070" },
        "3": { "text": "^", "fg": "#606060" },
    },
}, complete=True)
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
        }
    )


@override_style({
    "bullets": {
        "default": { "text": "*", "fg": "#505050" },
        "1": { "text": "-", "fg": "#808080" },
        "2": { "text": "=", "fg": "#707070" },
        "3": { "text": "^", "fg": "#606060" },
    },
}, complete=True)
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
        }
    )


@override_style({
    "numbering": {
        "default": { "text": "numeric", "fg": "italics" },
        "1": { "text": "numeric", "fg": "italics" },
        "2": { "text": "alpha", "fg": "bold" },
        "3": { "text": "roman", "fg": "underline" },
    },
    "bullets": {
        "default": { "text": "*", "fg": "italics" },
        "3": { "text": "^", "fg": "underline" },
    },
}, complete=True)
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
        }
    )


@override_style({
    "hrule": {
        "text": "=",
        "fg": "italics",
        "bg": "#004400",
    },
})
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
        }
    )


@override_style({
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
})
def test_block_quote(style):
    """Test block quote rendering"""
    utils.validate_render(
        md_text="""
            > Quote text
            > Quote italic text
            > Quote italic text
            > Quote italic text
            > Quote text
        """,
        text=[
            "██━━──               ",
            "┃  Quote text        ",
            "┃  Quote italic text ",
            "┃  Quote italic text ",
            "┃  Quote italic text ",
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
        }
    )


def test_code(tmpdir, mocker):
    """Test code block rendering"""
    setup_lookatme(
        tmpdir,
        mocker,
        style={
            "style": "monokai",
        },
    )

    rendered = render_markdown(
        """
```python
def some_fn(*args, **kargs):
    pass```
"""
    )

    stripped_rows = [
        b"",
        b"def some_fn(*args, **kargs):",
        b"    pass",
        b"",
    ]
    assert_render(stripped_rows, rendered)


def test_empty_codeblock(tmpdir, mocker):
    """Test that empty code blocks render correctly"""
    setup_lookatme(
        tmpdir,
        mocker,
        style={
            "style": "monokai",
        },
    )

    render_markdown(
        """
```python

```"""
    )


def test_code_yaml(tmpdir, mocker):
    """Test code block rendering with yaml language"""
    setup_lookatme(
        tmpdir,
        mocker,
        style={
            "style": "monokai",
        },
    )

    rendered = render_markdown(
        """
```yaml
test: a value
test2: "another value"
array:
  - item1
  - item2
  - item3
```"""
    )

    stripped_rows = [
        b"",
        b"test: a value",
        b'test2: "another value"',
        b"array:",
        b"  - item1",
        b"  - item2",
        b"  - item3",
        b"",
    ]
    assert_render(stripped_rows, rendered)


def test_inline(tmpdir, mocker):
    """Test inline markdown"""
    setup_lookatme(
        tmpdir,
        mocker,
        style={
            "style": "monokai",
            "link": {
                "fg": "underline",
                "bg": "default",
            },
        },
    )

    rendered = render_markdown("*emphasis*")
    assert rendered[0][0][0].foreground == "default,italics"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("**emphasis**")
    assert rendered[0][0][0].foreground == "default,bold"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("_emphasis_")
    assert rendered[0][0][0].foreground == "default,italics"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("__emphasis__")
    assert rendered[0][0][0].foreground == "default,bold"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("`inline code`")
    assert row_text(rendered[0]).rstrip() == b" inline code"

    rendered = render_markdown("~~strikethrough~~")
    assert rendered[0][0][0].foreground == "default,strikethrough"
    assert row_text(rendered[0]).rstrip() == b"strikethrough"

    rendered = render_markdown("[link](http://domain.tld)")
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"link"

    rendered = render_markdown("http://domain.tld")
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"http://domain.tld"

    rendered = render_markdown("![link](http://domain.tld)")
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"link"
