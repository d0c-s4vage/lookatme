"""
Test the file loader built-in extension
"""


import lookatme.config
import lookatme.contrib.file_loader as file_loader
import lookatme.render.pygments


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


def test_file_loader(tmpdir, mocker):
    """Test the built-in file loader extension
    """
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.render.pygments, "config", fake_config)
    fake_config.STYLE = TEST_STYLE

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
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.render.pygments, "config", fake_config)
    fake_config.STYLE = TEST_STYLE

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
    mocker.patch.object(lookatme.config, "LOG")
    mocker.patch.object(lookatme.config, "SLIDE_SOURCE_DIR", str(tmpdir))
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.render.pygments, "config", fake_config)
    fake_config.STYLE = TEST_STYLE

    tmppath = tmpdir.join("test.py")
    tmppath.write("print('hello')")

    rendered = render_markdown(f"""
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
    mocker.patch.object(lookatme.config, "LOG")
    fake_config = mocker.patch.object(lookatme.render.markdown_block, "config")
    mocker.patch.object(lookatme.render.pygments, "config", fake_config)
    fake_config.STYLE = TEST_STYLE

    rendered = render_markdown(f"""
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
