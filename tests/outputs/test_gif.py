"""
Test the gif output format
"""


import inspect
import os
from six.moves import StringIO  # type: ignore


from lookatme.pres import Presentation
import lookatme.output


def test_gif_output(tmpdir):
    """Ensure that gifs are created from slides"""
    md = inspect.cleandoc(
        r"""
    # Slide 1

    Testing 1

    # Slide 2

    Testing 2
    """
    )

    source = StringIO(md)
    pres = Presentation(source)
    output_path = str(tmpdir / "output.gif")
    lookatme.output.output_pres(pres, output_path, "gif", {})

    assert os.path.exists(output_path)
    assert os.stat(output_path).st_size > 0

    with open(output_path, "rb") as f:
        data = f.read()

    assert data.startswith(b"GIF89a") or data.startswith(b"GIF87a")
