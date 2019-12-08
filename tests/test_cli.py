"""
Test the main CLI
"""


from click.testing import CliRunner


import lookatme
from lookatme.__main__ import main


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
