"""
Test basic markdown renderings
"""


import urwid


import lookatme.config
import lookatme.render.markdown_block
import lookatme.render.pygments
from lookatme.parser import Parser
import lookatme.tui


from tests.utils import spec_and_text, row_text, render_markdown, assert_render


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
### H3
---
""")

    stripped_rows = [
        b"",
        b"|H1|",
        b"",
        b"|H2|",
        b"",
        b"|H3|",
        b"",
    ]
    assert_render(stripped_rows, rendered)


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

    stripped_rows = [
        b"H1        H2       H3",
        b"------- ------ ------",
        b"1value1 value2 value3",
        b"1          2        3",
    ]
    assert_render(stripped_rows, rendered, full_strip=True)


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

    stripped_rows = [
        b'',
        b'  - list 1',
        b'    = list 2',
        b'      ^ list 3',
        b'        * list 4',
        b'    = list 2',
        b'      ^ list 3',
        b'      ^ list 3',
        b'  - list 2',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_lists_with_newline(mocker):
    """Test list rendering with a newline between a new nested list and the
    previous list item
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
""")

    stripped_rows = [
        b'',
        b'  - list 1',
        b'',
        b'    = list 2',
        b'',
    ]
    assert_render(stripped_rows, rendered)

def test_numbered_lists(mocker):
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
        "numbering": {
            "default": "numeric",
            "1": "numeric",
            "2": "alpha",
            "3": "roman",
        },
    }

    rendered = render_markdown("""
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
""")

    stripped_rows = [
        b'',
        b'  1. list 1',
        b'     a. alpha1',
        b'     b. alpha2',
        b'     c. alpha3',
        b'  2. list 2',
        b'     a. alpha1.1',
        b'        i.   roman1',
        b'        ii.  roman2',
        b'        iii. roman3',
        b'     b. alpha1.2',
        b'        ^ test1',
        b'        ^ test2',
        b'  3. list 3',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_hrule(mocker):
    """Test that hrules render correctly
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    fake_config.STYLE = {
        "hrule": {
            "style": {
                "fg": "",
                "bg": "",
            },
            "char": "=",
        },
    }

    rendered = render_markdown("---", width=10, single_slide=True)
    stripped_rows = [
        b'',
        b'==========',
        b'',
    ]
    assert_render(stripped_rows, rendered)


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

    stripped_rows = [
        b'',
        b'-',
        b'>  this is a quote',
        b'=',
        b'',
    ]
    assert_render(stripped_rows, rendered)

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

    stripped_rows = [
        b'',
        b'def some_fn(*args, **kargs):',
        b'    pass',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_empty_codeblock(mocker):
    """Test that empty code blocks render correctly
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.pygments, "config")
    fake_config.STYLE = {
        "style": "monokai",
    }

    rendered = render_markdown("""
```python

```""")


def test_code_yaml(mocker):
    """Test code block rendering with yaml language
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.pygments, "config")
    fake_config.STYLE = {
        "style": "monokai",
    }

    rendered = render_markdown("""
```yaml
test: a value
test2: "another value"
array:
  - item1
  - item2
  - item3
```""")

    stripped_rows = [
        b'',
        b'test: a value',
        b'test2: "another value"',
        b'array:',
        b'  - item1',
        b'  - item2',
        b'  - item3',
        b'',
    ]
    assert_render(stripped_rows, rendered)


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
    assert rendered[1][0][0].foreground == "default,italics"
    assert row_text(rendered[1]).strip() == b"emphasis"

    rendered = render_markdown("**emphasis**")
    assert rendered[1][0][0].foreground == "default,underline"
    assert row_text(rendered[1]).strip() == b"emphasis"

    rendered = render_markdown("_emphasis_")
    assert rendered[1][0][0].foreground == "default,italics"
    assert row_text(rendered[1]).strip() == b"emphasis"

    rendered = render_markdown("__emphasis__")
    assert rendered[1][0][0].foreground == "default,underline"
    assert row_text(rendered[1]).strip() == b"emphasis"

    rendered = render_markdown("`inline code`")
    assert row_text(rendered[1]).rstrip() == b" inline code"

    rendered = render_markdown("~~strikethrough~~")
    assert rendered[1][0][0].foreground == "default,strikethrough"
    assert row_text(rendered[1]).rstrip() == b"strikethrough"

    rendered = render_markdown("[link](http://domain.tld)")
    assert rendered[1][0][0].foreground == "default,underline"
    assert row_text(rendered[1]).rstrip() == b"link"

    rendered = render_markdown("http://domain.tld")
    assert rendered[1][0][0].foreground == "default,underline"
    assert row_text(rendered[1]).rstrip() == b"http://domain.tld"

    rendered = render_markdown("![link](http://domain.tld)")
    assert rendered[1][0][0].foreground == "default,underline"
    assert row_text(rendered[1]).rstrip() == b"link"

#      rendered = render_markdown("""
#  test[^1]
#  [^1]: This is a foot note
#  """)
#      assert len(rendered) == 1
#      assert rendered[0][0][0].foreground == "default,underline"
#      assert row_text(rendered[0]).rstrip() == b"link"
#  
