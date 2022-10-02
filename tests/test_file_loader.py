"""
Test the file loader built-in extension
"""


import pytest

import lookatme.config
import lookatme.contrib.file_loader
import lookatme.render.pygments
from tests.utils import assert_render, render_markdown

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


@pytest.fixture(autouse=True)
def file_loader_setup(tmpdir, mocker):
    mocker.patch.object(lookatme.config, "LOG")
    mocker.patch("lookatme.config.SLIDE_SOURCE_DIR", new=str(tmpdir))
    mocker.patch("lookatme.contrib.CONTRIB_MODULES", new=[
        lookatme.contrib.file_loader
    ])
    mocker.patch("lookatme.config.STYLE", new=TEST_STYLE)


def test_file_loader(tmpdir, mocker):
    """Test the built-in file loader extension
    """
    tmppath = tmpdir.join("test.py")
    tmppath.write("print('hello')")

    rendered = render_markdown(f"""
```file
path: {tmppath}
relative: false
```
    """)

    stripped_rows = [
        b'',
        b"print('hello')",
        b'',
        b'',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_file_loader_with_transform(tmpdir, mocker):
    """Test the built-in file loader extension
    """
    tmppath = tmpdir.join("test.py")
    tmppath.write("""
Hello
Apples2
there
Apples3
there
Apples1
""")

    rendered = render_markdown(f"""
```file
path: {tmppath}
relative: false
transform: "grep -i apples | sort"
```
    """)

    stripped_rows = [
        b'',
        b"Apples1",
        b'Apples2',
        b'Apples3',
        b'',
        b'',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_file_loader_relative(tmpdir, mocker):
    """Test the built-in file loader extension
    """
    tmppath = tmpdir.join("test.py")
    tmppath.write("print('hello')")

    rendered = render_markdown("""
```file
path: test.py
relative: true
```
    """)

    stripped_rows = [
        b'',
        b"print('hello')",
        b'',
        b'',
        b'',
    ]
    assert_render(stripped_rows, rendered)


def test_file_loader_not_found(mocker):
    """Test the built-in file loader extension
    """
    rendered = render_markdown("""
```file
path: does_not_exist.py
```
    """)

    stripped_rows = [
        b'',
        b"File not found",
        b'',
        b'',
        b'',
    ]
    assert_render(stripped_rows, rendered)
