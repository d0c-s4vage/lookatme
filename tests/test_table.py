"""
This module tests the Table widget in lookatme/widgets/table.py
"""


import pytest
from typing import Any, Dict, List, Tuple, Optional
import urwid

import lookatme.parser
import lookatme.render.markdown_block as markdown_block
from lookatme.render.context import Context
from lookatme.widgets.table import Table
import tests.utils as utils


TEST_STYLE = {
    "style": "monokai",
    "table": {
        "bg": "",
        "fg": "",
        "column_spacing": 1,
        "even_rows": {"bg": "", "fg": ""},
        "header": {"bg": "#202020", "fg": "bold"},
        "header_divider": {"bg": "", "fg": "bold", "text": "─"},
        "odd_rows": {"bg": "#181818", "fg": ""},
    },
}


@pytest.fixture(autouse=True)
def table_setup(tmpdir, mocker):
    utils.setup_lookatme(tmpdir, mocker, style=TEST_STYLE)


def _md_to_table_tokens(md_text: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    tokens = lookatme.parser.md_to_tokens(md_text)
    # skip the table_open token and the table_close tokens
    extractor = markdown_block.TableTokenExtractor()
    return extractor.process_tokens(tokens[1:-1])


def _render_table(
    md_text: str,
) -> Tuple[Table, List[List[Tuple[Optional[urwid.AttrSpec], Any, bytes]]]]:
    thead, tbody = _md_to_table_tokens(md_text)
    assert thead is not None
    assert tbody is not None

    ctx = Context(None)
    root = urwid.Pile([])
    table = Table(ctx, thead, tbody)
    padding = urwid.Padding(root, width=table.total_width)
    with ctx.use_tokens([{}]):
        with ctx.use_container(root, is_new_block=True):
            ctx.widget_add(table)

    content = list(padding.render((table.total_width,), False).content())
    return table, content


def test_basic_render(table_setup):
    """Test that a Table widget renders correctly"""
    table, content = _render_table(
        r"""
| H1 | H2 | H3  |
|----|:--:|----:|
| 1  | 22 | 333 |
| 1  | 22 | 333 |
    """
    )
    spacing = TEST_STYLE["table"]["column_spacing"]

    # four rows: headers, divider, row1, row2
    assert len(content) == 4
    assert dict(table.column_maxes) == {0: 2, 1: 2, 2: 3}
    assert table.cell_spacing == spacing
    assert table.total_width == len("H1H2333") + 2 * spacing

    utils.validate_render(
        rendered=content,
        text=[
            "H1 H2  H3",
            "─────────",
            "1  22 333",
            "1  22 333",
        ],
        style_mask=[
            "HHHHHHHHH",
            "HHHHHHHHH",
            "EEEEEEEEE",  # even row
            "OOOOOOOOO",  # odd row
        ],
        styles={
            "H": TEST_STYLE["table"]["header"],
            "O": TEST_STYLE["table"]["odd_rows"],
            "E": TEST_STYLE["table"]["even_rows"],
        },
    )


def test_ignore_extra_columns_render(table_setup):
    """Test that a Table widget renders correctly"""
    table, content = _render_table(
        r"""
| H1 | H2 | H3  |
|----|:--:|----:|
| 1  | 22 | 333 | 444 |
| 1  | 22 | 333 | 555 | 666666 |
    """
    )
    spacing = TEST_STYLE["table"]["column_spacing"]

    # four rows: headers, divider, row1, row2
    assert len(content) == 4
    assert dict(table.column_maxes) == {0: 2, 1: 2, 2: 3}
    assert table.cell_spacing == spacing
    assert table.total_width == len("H1H2333") + 2 * spacing

    utils.validate_render(
        rendered=content,
        text=[
            "H1 H2  H3",
            "─────────",
            "1  22 333",
            "1  22 333",
        ],
        style_mask=[
            "HHHHHHHHH",
            "HHHHHHHHH",
            "EEEEEEEEE",  # even row
            "OOOOOOOOO",  # odd row
        ],
        styles={
            "H": TEST_STYLE["table"]["header"],
            "O": TEST_STYLE["table"]["odd_rows"],
            "E": TEST_STYLE["table"]["even_rows"],
        },
    )


def test_default_left_align(table_setup):
    """Test that default (left) align works"""
    table, content = _render_table(
        r"""
| H1 | H2 | H3  |
|----|----|-----|
| 1  | 22 | 333 |
| 1  | 22 | 333 |
    """
    )
    spacing = TEST_STYLE["table"]["column_spacing"]

    # four rows: headers, divider, row1, row2
    assert len(content) == 4
    assert dict(table.column_maxes) == {0: 2, 1: 2, 2: 3}
    assert table.cell_spacing == spacing
    assert table.total_width == len("H1H2333") + 2 * spacing

    utils.validate_render(
        rendered=content,
        text=[
            "H1 H2 H3 ",
            "─────────",
            "1  22 333",
            "1  22 333",
        ],
        style_mask=[
            "HHHHHHHHH",
            "HHHHHHHHH",
            "EEEEEEEEE",  # even row
            "OOOOOOOOO",  # odd row
        ],
        styles={
            "H": TEST_STYLE["table"]["header"],
            "O": TEST_STYLE["table"]["odd_rows"],
            "E": TEST_STYLE["table"]["even_rows"],
        },
    )


def test_left_align(table_setup):
    """Test that default (left) align works"""
    table, content = _render_table(
        r"""
| H1 | H2 | H3  |
|:---|:---|:----|
| 1  | 22 | 333 |
| 1  | 22 | 333 |
    """
    )
    spacing = TEST_STYLE["table"]["column_spacing"]

    # four rows: headers, divider, row1, row2
    assert len(content) == 4
    assert dict(table.column_maxes) == {0: 2, 1: 2, 2: 3}
    assert table.cell_spacing == spacing
    assert table.total_width == len("H1H2333") + 2 * spacing

    utils.validate_render(
        rendered=content,
        text=[
            "H1 H2 H3 ",
            "─────────",
            "1  22 333",
            "1  22 333",
        ],
        style_mask=[
            "HHHHHHHHH",
            "HHHHHHHHH",
            "EEEEEEEEE",  # even row
            "OOOOOOOOO",  # odd row
        ],
        styles={
            "H": TEST_STYLE["table"]["header"],
            "O": TEST_STYLE["table"]["odd_rows"],
            "E": TEST_STYLE["table"]["even_rows"],
        },
    )


def test_center_align(table_setup):
    """Test that default (left) align works"""
    table, content = _render_table(
        r"""
| H1     | H2   | H3  |
|:------:|:----:|:---:|
| 1      | 22   | 333 |
| 11111  | 2233 | 333 |
    """
    )
    spacing = TEST_STYLE["table"]["column_spacing"]

    # four rows: headers, divider, row1, row2
    assert len(content) == 4
    assert dict(table.column_maxes) == {0: 5, 1: 4, 2: 3}
    assert table.cell_spacing == spacing
    assert table.total_width == len("111112233333") + 2 * spacing

    utils.validate_render(
        rendered=content,
        text=[
            "  H1   H2   H3",
            "──────────────",
            "  1    22  333",
            "11111 2233 333",
        ],
        style_mask=[
            "HHHHHHHHHHHHHH",
            "HHHHHHHHHHHHHH",
            "EEEEEEEEEEEEEE",  # even row
            "OOOOOOOOOOOOOO",  # odd row
        ],
        styles={
            "H": TEST_STYLE["table"]["header"],
            "O": TEST_STYLE["table"]["odd_rows"],
            "E": TEST_STYLE["table"]["even_rows"],
        },
    )
