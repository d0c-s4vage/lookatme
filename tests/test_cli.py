"""
Test the main CLI
"""


from typing import Optional

import yaml
from click.testing import CliRunner

import lookatme
import lookatme.schemas
import lookatme.themes.dark as dark_theme
import lookatme.themes.light as light_theme
import lookatme.tui
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


def _get_dumped_style(
    tmpdir,
    theme: Optional[str] = None,
    md_meta_style: Optional[str] = None,
    cli_style: Optional[str] = None
) -> str:
    cli_args = ["--dump-styles"]

    if theme is not None:
        cli_args += ["--theme", theme]
    if md_meta_style is not None:
        tmpfile = tmpdir.join("test.md")
        with open(tmpfile, "w") as f:
            f.write("\n".join([
                "---",
                "styles:",
                "  style: {}".format(md_meta_style),
                "---",
            ]))
        cli_args += [str(tmpfile)]
    if cli_style is not None:
        cli_args += ["--style", cli_style]

    res = run_cmd(*cli_args)
    assert res.exit_code == 0

    yaml_data = yaml.safe_load(res.output)
    return yaml_data["style"]


def test_style_override_precedence_dark(tmpdir):
    """Test that dump styles works correctly
    """
    default_style = _get_dumped_style(tmpdir)
    themed_style = _get_dumped_style(tmpdir, theme="dark")
    themed_and_md = _get_dumped_style(
        tmpdir,
        theme="dark",
        md_meta_style="emacs"
    )
    themed_and_md_and_cli = _get_dumped_style(
        tmpdir,
        theme="dark",
        md_meta_style="emacs",
        cli_style="zenburn"
    )

    default = lookatme.schemas.MetaSchema().dump(None)
    assert default_style == default["styles"]["style"]

    dark_theme_styles = lookatme.schemas.StyleSchema().dump(dark_theme.theme)
    assert themed_style == dark_theme_styles["style"]  # type: ignore

    assert themed_and_md == "emacs"
    assert themed_and_md_and_cli == "zenburn"


def test_style_override_precedence_light(tmpdir):
    """Test that dump styles works correctly
    """
    default_style = _get_dumped_style(tmpdir)
    themed_style = _get_dumped_style(tmpdir, theme="light")
    themed_and_md = _get_dumped_style(
        tmpdir,
        theme="light",
        md_meta_style="emacs"
    )
    themed_and_md_and_cli = _get_dumped_style(
        tmpdir,
        theme="light",
        md_meta_style="emacs",
        cli_style="zenburn"
    )

    default = lookatme.schemas.MetaSchema().dump(None)
    assert default_style == default["styles"]["style"]

    light_theme_styles = lookatme.schemas.StyleSchema().dump(light_theme.theme)
    assert themed_style == light_theme_styles["style"]  # type: ignore

    assert themed_and_md == "emacs"
    assert themed_and_md_and_cli == "zenburn"


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
