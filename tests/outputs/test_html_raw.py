"""
This module tests the html_raw output type
"""


import inspect
import glob
import os
import re
from six.moves import StringIO  # type: ignore

import lookatme.output
from lookatme.pres import Presentation


def test_html_raw_output_defined():
    assert "html_raw" in lookatme.output.get_all_formats()


def test_basic_raw_slide_generation(tmpdir):
    md = inspect.cleandoc(
        r"""
        # Slide 1

        Hello world

        # Slide 2

        {}

        # Slide 3

        FIN
    """
    ).format("A\n\n" * 100)

    delay_default = 973
    delay_scroll = 53
    cols = 88
    rows = 27
    keys = ["j:30", "j"]
    render_images = False

    options = lookatme.output.parse_options(
        [
            f"html_raw.delay_default={delay_default}",
            f"html_raw.delay_scroll={delay_scroll}",
            f"html_raw.cols={cols}",
            f"html_raw.rows={rows}",
            f"html_raw.keys={','.join(keys)}",
            f"html_raw.render_images={render_images}",
        ]
    )

    pres = Presentation(StringIO(md))
    lookatme.output.output_pres(pres, str(tmpdir), "html_raw", options)

    html_files = glob.glob(str(tmpdir / "*.html"))
    html_files.sort()
    assert len(html_files) == 3

    expected_infos = [
        {"screen": "0", "delay": str(delay_default), "key": ""},
        {"screen": "1", "delay": "30", "key": "j"},
        {"screen": "2", "delay": str(delay_default), "key": "j"},
    ]
    for idx, file in enumerate(html_files):
        file_noext, _ = os.path.splitext(os.path.basename(file))
        info = dict(
            re.findall(r"(?:^|_)(?P<attr>[a-zA-Z]+):(?P<val>[^_\.]*)", file_noext)
        )
        assert info == expected_infos[idx]

        with open(file, "r") as f:
            data = f.read()

        assert f"Slide {idx + 1}" in data
        assert f"slide {idx + 1} / {len(html_files)}" in data

        assert data.count("<br/>") == rows - 1
        lines = data.split("<br/>")

        total_spaces = 0
        for match in re.finditer(r"style='padding-left: (\d+)ch'", lines[1]):
            total_spaces += int(match.group(1))

        assert total_spaces == cols
