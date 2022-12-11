"""
Test the file loader built-in extension
"""


import pytest

import lookatme.config
import lookatme.contrib.file_loader
import tests.utils as utils
from tests.utils import override_style


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
def file_loader_setup(mocker):
    mocker.patch("lookatme.contrib.CONTRIB_MODULES", new=[lookatme.contrib.file_loader])


@override_style({}, pass_tmpdir=True)
def test_file_loader(tmpdir, _):
    """Test the built-in file loader extension"""
    tmppath = tmpdir.join("test.py")
    tmppath.write("'hello'")

    utils.validate_render(
        md_text=f"""
            ```file
            path: {tmppath}
            relative: false
            ```
        """,
        text=[
            "'hello'",
        ],
        style_mask=[
            "SSSSSSS",
        ],
        styles={
            "S": {"fg": "#f8f8f2", "bg": "#272822"},
        },
    )


@override_style({}, pass_tmpdir=True)
def test_file_loader_with_transform(tmpdir, _):
    """Test the built-in file loader extension"""
    tmppath = tmpdir.join("test.py")
    tmppath.write(
        """
Hello
Apples2
there
Apples3
there
Apples1
"""
    )

    utils.validate_render(
        md_text=f"""
            ```file
            path: {tmppath}
            relative: false
            transform: "grep -i apples | sort"
            ```
        """,
        text=[
            "Apples1",
            "Apples2",
            "Apples3",
        ],
        style_mask=[
            "TTTTTTT",
            "TTTTTTT",
            "TTTTTTT",
        ],
        styles={
            "T": {"fg": "#f8f8f2", "bg": "#272822"},
        },
    )


@override_style({}, pass_tmpdir=True)
def test_file_loader_relative(tmpdir, _):
    """Test the built-in file loader extension"""
    tmppath = tmpdir.join("test.py")
    tmppath.write("'hello'")

    utils.validate_render(
        md_text="""
            ```file
            path: test.py
            relative: true
            ```
        """,
        text=[
            "'hello'",
        ],
        style_mask=[
            "SSSSSSS",
        ],
        styles={
            "S": {"fg": "#f8f8f2", "bg": "#272822"},
        },
    )


@override_style({})
def test_file_loader_not_found(_):
    """Test the built-in file loader extension"""
    utils.validate_render(
        md_text="""
            ```file
            path: does_not_exist.py
            ```
        """,
        text=[
            "File not found",
        ],
        style_mask=[
            "TTTTTTTTTTTTTT",
        ],
        styles={
            "T": {"fg": "#f8f8f2", "bg": "#272822"},
        },
    )
