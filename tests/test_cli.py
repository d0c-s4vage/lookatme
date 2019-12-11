"""
Test the main CLI
"""


from click.testing import CliRunner


import lookatme
from lookatme.__main__ import main
import lookatme.tui


def run_cmd(*args):
    """Run the provided arguments
    """
    runner = CliRunner()
    return runner.invoke(main, args)


def test_dump_styles_unicode():
    """Test that dump styles works correctly
    """
    res = run_cmd("--dump-styles")
    assert res.exit_code == 0
    assert "█" in res.output


def test_version():
    """Test the version option
    """
    res = run_cmd("--version")
    assert res.exit_code == 0
    assert lookatme.__version__ in res.output


def test_exceptions(tmpdir, mocker):
    """Test exception handling on invalid inputs
    """
    log_path = tmpdir.join("log.txt")
    pres_path = tmpdir.join("test.md")
    with pres_path.open("w") as f:
        f.write("# Hello")

    slide_number = 3
    exception_text = "EXCEPTION TEXT"

    def fake_create_tui(*args, **kwargs):
        res = mocker.MagicMock()
        res.curr_slide.number = slide_number
        res.run.side_effect = Exception(exception_text)
        return res
    mocker.patch.object(lookatme.tui, "create_tui", fake_create_tui)

    res = run_cmd("--log", str(log_path), str(pres_path))
    assert exception_text in res.output
    assert f"slide {slide_number+1}" in res.output
    # should remind us to rerun with --debug to see the traceback
    assert "--debug" in res.output

    res = run_cmd("--debug", "--log", str(log_path), str(pres_path))
    assert exception_text in res.output
    assert f"slide {slide_number+1}" in res.output
    # should remind us to check log_path for the traceback
    assert str(log_path) in res.output
