"""
Test basic markdown renderings
"""


import urwid


import lookatme.config
import lookatme.render.markdown_block
import lookatme.render.pygments
from lookatme.parser import Parser
import lookatme.tui


from tests.utils import spec_and_text, row_text


def render_markdown(markdown, height=50):
    """Returns the rendered canvas contents of the markdown
    """
    loop = urwid.MainLoop(urwid.Pile([]))
    renderer = lookatme.tui.SlideRenderer(loop)
    renderer.start()

    parser = Parser()
    _, slides = parser.parse_slides(markdown)

    renderer.stop()
    pile_contents = renderer.render_slide(slides[0], force=True)
    renderer.join()

    pile = urwid.Pile([urwid.Text("testing")])
    pile.contents = pile_contents
    return list(pile.render((height,)).content())


TEST_STYLE = {
    "style": "monokai",
    "headings": {
        "default": {
            "fg": "bold",
            "bg": "",
            "prefix": "|",
            "suffix": "|",
        },
    },
}


def test_headings(mocker):
    """Test basic header rendering
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    fake_config.STYLE = TEST_STYLE

    rendered = render_markdown("""
# H1
## H2
### H3""")

    # three lines for the headings plus an extra line of padding after each
    # and one line of padding before the first one
    assert len(rendered) == 7

    stripped_rows = [
        b"",
        b"|H1|",
        b"",
        b"|H2|",
        b"",
        b"|H3|",
        b"",
    ]
    for idx, row in enumerate(rendered):
        stripped_row_text = row_text(row).strip()
        assert stripped_row_text == stripped_rows[idx]


def test_table(mocker):
    """Test basic table rendering
    """
    import lookatme.widgets.table

    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.widgets.table, "config", fake_config)
    fake_config.STYLE = {
        "table": {
            "column_spacing": 1,
            "header_divider": "-",
        },
    }

    rendered = render_markdown("""
| H1      |   H2   |     H3 |
|:--------|:------:|-------:|
| 1value1 | value2 | value3 |
| 1       | 2      | 3      |
""")

    assert len(rendered) == 4

    stripped_rows = [
        b"H1        H2       H3",
        b"------- ------ ------",
        b"1value1 value2 value3",
        b"1          2        3",
    ]
    for idx, row in enumerate(rendered):
        stripped_row_text = row_text(row).strip()
        assert stripped_row_text == stripped_rows[idx]


def test_lists(mocker):
    """Test list rendering
    """
    import lookatme.widgets.table

    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.widgets.table, "config", fake_config)
    fake_config.STYLE = {
        "bullets": {
            "default": "*",
            "1": "-",
            "2": "=",
            "3": "^",
        },
    }

    rendered = render_markdown("""
* list 1
  * list 2
    * list 3
      * list 4
  * list 2
    * list 3
    * list 3

* list 2
""")

    # seven list items plus a pre and post Divider()
    assert len(rendered) == 10

    stripped_rows = [
        b'',
        b'  - list 1',
        b'      = list 2',
        b'          ^ list 3',
        b'              * list 4',
        b'      = list 2',
        b'          ^ list 3',
        b'          ^ list 3',
        b'  - list 2',
        b'',
    ]
    for idx, row in enumerate(rendered):
        stripped_row_text = row_text(row).rstrip()
        assert stripped_row_text == stripped_rows[idx]


def test_block_quote(mocker):
    """Test block quote rendering
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    fake_config.STYLE = {
        "quote": {
            "style": {
                "fg": "",
                "bg": "",
            },
            "side": ">",
            "top_corner": "-",
            "bottom_corner": "=",
        },
    }

    rendered = render_markdown("""
> this is a quote
""")

    assert len(rendered) == 5

    stripped_rows = [
        b'',
        b'-',
        b'>  this is a quote',
        b'=',
        b'',
    ]
    for idx, row in enumerate(rendered):
        stripped_row_text = row_text(row).rstrip()
        assert stripped_row_text == stripped_rows[idx]

def test_code(mocker):
    """Test code block rendering
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.pygments, "config")
    fake_config.STYLE = {
        "style": "monokai",
    }

    rendered = render_markdown("""
```python
def some_fn(*args, **kargs):
    pass```
    """)

    assert len(rendered) == 5

    stripped_rows = [
        b'',
        b'def some_fn(*args, **kargs):',
        b'    pass',
        b'',
        b'',
    ]
    for idx, row in enumerate(rendered):
        stripped_row_text = row_text(row).rstrip()
        assert stripped_row_text == stripped_rows[idx]


def test_inline(mocker):
    """Test inline markdown
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.pygments, "config")
    mocker.patch.object(lookatme.render.markdown_inline, "config", fake_config)
    fake_config.STYLE = {
        "style": "monokai",
        "link": {
            "fg": "underline",
            "bg": "default",
        },
    }

    rendered = render_markdown("*emphasis*")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,italics"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("**emphasis**")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("_emphasis_")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,italics"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("__emphasis__")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).strip() == b"emphasis"

    rendered = render_markdown("`inline code`")
    assert len(rendered) == 1
    assert row_text(rendered[0]).rstrip() == b" inline code"

    rendered = render_markdown("~~strikethrough~~")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,strikethrough"
    assert row_text(rendered[0]).rstrip() == b"strikethrough"

    rendered = render_markdown("[link](http://domain.tld)")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"link"

    rendered = render_markdown("http://domain.tld")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"http://domain.tld"

    rendered = render_markdown("![link](http://domain.tld)")
    assert len(rendered) == 1
    assert rendered[0][0][0].foreground == "default,underline"
    assert row_text(rendered[0]).rstrip() == b"link"

#      rendered = render_markdown("""
#  test[^1]
#  [^1]: This is a foot note
#  """)
#      assert len(rendered) == 1
#      assert rendered[0][0][0].foreground == "default,underline"
#      assert row_text(rendered[0]).rstrip() == b"link"
#  
