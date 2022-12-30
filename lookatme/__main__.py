#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import io
import os
import tempfile

import click
import pygments.styles

import lookatme
import lookatme.config
import lookatme.log
import lookatme.tui
import lookatme.tutorial
from lookatme.pres import Presentation
from lookatme.schemas import StyleSchema


@click.command("lookatme")
@click.option("--debug", "debug", is_flag=True, default=False)
@click.option(
    "-l",
    "--log",
    "log_path",
    type=click.Path(writable=True),
    default=os.path.join(tempfile.gettempdir(), "lookatme.log"),
)
@click.option(
    "--tutorial",
    "tutorial",
    is_flag=False,
    flag_value="all",
    show_default=True,
    help=(
        "As a flag: show all tutorials. "
        "With a value/comma-separated values: show the specific tutorials. "
        "Use the value 'help' for more help"
    )
)
@click.option(
    "-t",
    "--theme",
    "theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
)
@click.option(
    "--style",
    "code_style",
    default=None,
    type=click.Choice(list(pygments.styles.get_all_styles())),
)
@click.option(
    "--dump-styles",
    help="Dump the resolved styles that will be used with the presentation to stdout",
    is_flag=True,
    default=False,
)
@click.option(
    "--live",
    "--live-reload",
    "live_reload",
    help="Watch the input filename for modifications and automatically reload",
    is_flag=True,
    default=False,
)
@click.option(
    "-s",
    "--safe",
    help="Do not load any new extensions specified in the source markdown. "
         "Extensions specified via env var or -e are still loaded",
    is_flag=True,
    default=False,
)
@click.option(
    "--no-ext-warn",
    help="Load new extensions specified in the source markdown without warning",
    is_flag=True,
    default=False,
)
@click.option(
    "-i",
    "--ignore-ext-failure",
    help="Ignore load failures of extensions",
    is_flag=True,
    default=False,
)
@click.option(
    "-e",
    "--exts",
    "extensions",
    help="A comma-separated list of extension names to automatically load"
         " (LOOKATME_EXTS)",
    envvar="LOOKATME_EXTS",
    default="",
)
@click.option(
    "--single",
    "--one",
    "single_slide",
    help="Render the source as a single slide",
    is_flag=True,
    default=False
)
@click.version_option(lookatme.__version__)
@click.argument(
    "input_files",
    type=click.File("r"),
    nargs=-1,
)
def main(tutorial, debug, log_path, theme, code_style, dump_styles,
         input_files, live_reload, extensions, single_slide, safe, no_ext_warn,
         ignore_ext_failure):
    """lookatme - An interactive, terminal-based markdown presentation tool.

    See https://lookatme.readthedocs.io/en/v2.5.5 for documentation
    """
    if debug:
        lookatme.config.LOG = lookatme.log.create_log(log_path)
    else:
        lookatme.config.LOG = lookatme.log.create_null_log()

    if len(input_files) == 0:
        input_files = [io.StringIO("")]

    if tutorial:
        if tutorial == "all":
            tutors = ["general", "markdown"]
        else:
            tutors = [x.strip() for x in tutorial.split(",")]

        theme_mod = __import__("lookatme.themes." + theme, fromlist=[theme])
        lookatme.config.set_global_style_with_precedence(
            theme_mod,
            {},
            code_style,
        )
        tutorial_md = lookatme.tutorial.get_tutorial_md(tutors)
        if tutorial_md is None:
            lookatme.tutorial.print_tutorial_help()
            return 1

        input_files = [io.StringIO(tutorial_md)]

    preload_exts = [x.strip() for x in extensions.split(",")]
    preload_exts = list(filter(lambda x: x != "", preload_exts))
    pres = Presentation(
        input_files[0],
        theme,
        code_style,
        live_reload=live_reload,
        single_slide=single_slide,
        preload_extensions=preload_exts,
        safe=safe,
        no_ext_warn=no_ext_warn,
        ignore_ext_failure=ignore_ext_failure,
    )

    if dump_styles:
        print(StyleSchema().dumps(pres.styles))
        return 0

    try:
        pres.run()
    except Exception as e:
        number = pres.get_tui().curr_slide.number + 1
        click.echo(f"Error rendering slide {number}: {e}")
        if not debug:
            click.echo("Rerun with --debug to view the full traceback in logs")
        else:
            lookatme.config.get_log().exception(
                f"Error rendering slide {number}: {e}")
            click.echo(f"See {log_path} for traceback")
        raise click.Abort()


if __name__ == "__main__":
    main()
