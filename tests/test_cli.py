"""
Test the main CLI
"""


from click.testing import CliRunner


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
