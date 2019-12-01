"""
This module tests the Table widget in lookatme/widgets/table.py
"""


import lookatme.widgets.table


from tests.utils import *


def test_basic_render(mocker):
    """Test that a Table widget renders correctly
    """
    column_spacing = 3

    fake_config = mocker.patch.object(lookatme.widgets.table, "config")
    fake_config.STYLE = {
        "style": "monokai",
        "table": {
            "column_spacing": column_spacing,
            "header_divider": "&",
        },
    }

    headers = ["H1", "H2", "H3"]
    aligns = ["left", "center", "right"]
    rows = [
        ["1", "22", "333"],
        ["*1*", "~~22~~", "**333**"],
    ]

    table = lookatme.widgets.table.Table(rows, headers=headers, aligns=aligns)
    canvas = table.render((20,))
    content = list(canvas.content())

    # four rows:
    #  1 headers
    #  2 DIVIDER
    #  3 row1
    #  4 row2
    assert len(content) == 4

    header_row = content[0]
    spec, text = spec_and_text(header_row[0])
    assert "bold" in spec.foreground
    assert text == b"H1"
    spec, text = spec_and_text(header_row[2])
    assert "bold" in spec.foreground
    assert text == b"H2"
    spec, text = spec_and_text(header_row[5])
    assert "bold" in spec.foreground
    assert text == b"H3"

    divider_row = content[1]
    spec, text = spec_and_text(divider_row[0])
    # no styling applied to the divider
    assert spec is None
    assert text == b"&&"
    spec, text = spec_and_text(divider_row[2])
    # no styling applied to the divider
    assert spec is None
    assert text == b"&&"
    spec, text = spec_and_text(divider_row[4])
    # no styling applied to the divider
    assert spec is None
    assert text == b"&&&"

    content_row1 = content[2]
    spec, text = spec_and_text(content_row1[0])
    # no styling applied to this row
    assert spec is None
    assert text == b"1 "
    spec, text = spec_and_text(content_row1[2])
    # no styling applied to this row
    assert spec is None
    assert text == b"22"
    spec, text = spec_and_text(content_row1[4])
    # no styling applied to this row
    assert spec is None
    assert text == b"333"

    content_row1 = content[3]
    spec, text = spec_and_text(content_row1[0])
    # no styling applied to this row
    assert "italics" in spec.foreground
    assert text == b"1"
    spec, text = spec_and_text(content_row1[3])
    # no styling applied to this row
    assert "strikethrough" in spec.foreground
    assert text == b"22"
    spec, text = spec_and_text(content_row1[5])
    # no styling applied to this row
    assert "underline" in spec.foreground
    assert text == b"333"


def test_table_no_headers(mocker):
    """This situation could never happen as parsed from Markdown. See
    https://stackoverflow.com/a/17543474.
    
    However this situation could happen manually when using the Table() class
    directly.
    """
    fake_config = mocker.patch.object(lookatme.widgets.table, "config")
    fake_config.STYLE = {
        "style": "monokai",
        "table": {
            "column_spacing": 3,
            "header_divider": "&",
        },
    }

    headers = None
    aligns = ["left", "center", "right"]
    rows = [
        ["1", "22", "333"],
        ["*1*", "~~22~~", "**333**"],
    ]

    table = lookatme.widgets.table.Table(rows, headers=headers, aligns=aligns)
    canvas = table.render((20,))
    content = list(canvas.content())

    assert len(content) == 2


def test_ignored_extra_column(mocker):
    """Test that extra columns beyond header values are ignored
    """
    fake_config = mocker.patch.object(lookatme.widgets.table, "config")
    fake_config.STYLE = {
        "style": "monokai",
        "table": {
            "column_spacing": 3,
            "header_divider": "&",
        },
    }

    headers = ["H1", "H2", "H3"]
    aligns = ["left", "center", "right"]
    rows = [
        ["1", "2", "3"],
        ["1", "2", "3", "4"],
        ["1", "2", "3", "4", "5"],
    ]

    table = lookatme.widgets.table.Table(rows, headers=headers, aligns=aligns)
    canvas = table.render((20,))
    content = list(canvas.content())

    # number of rows of output
    assert len(content) == 5
    assert b"4" not in row_text(content[-2])

    assert b"4" not in row_text(content[-1])
    assert b"5" not in row_text(content[-1])
