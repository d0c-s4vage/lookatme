#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import click
import logging
import io
import os
import pygments.styles
import sys
import tempfile


import lookatme.tui
import lookatme.log
import lookatme.config
from lookatme.pres import Presentation
from lookatme.schemas import StyleSchema


@click.command("lookatme")
@click.option("--debug", "debug", is_flag="True", default=False)
@click.option(
    "-l",
    "--log",
    "log_path",
    type=click.Path(writable=True),
    default=os.path.join(tempfile.gettempdir(), "lookatme.log"),
)
@click.option(
    "-t",
    "--theme",
    "theme",
    type=click.Choice(["dark", "light"]),
    default="dark",
)
@click.option(
    "-s",
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
def main(debug, log_path, theme, code_style, dump_styles, input_files, live_reload, single_slide):
    """lookatme - An interactive, terminal-based markdown presentation tool.
    """
    if debug:
        lookatme.config.LOG = lookatme.log.create_log(log_path)
    else:
        lookatme.config.LOG = lookatme.log.create_null_log()

    if len(input_files) == 0:
        input_files = [io.StringIO("")]
    pres = Presentation(
        input_files[0],
        theme,
        code_style,
        live_reload=live_reload,
        single_slide=single_slide
    )

    if dump_styles:
        print(StyleSchema().dumps(pres.styles))
        return 0

    try:
        pres.run()
    except Exception as e:
        number = pres.tui.curr_slide.number + 1
        click.echo(f"Error rendering slide {number}: {e}")
        if not debug:
            click.echo("Rerun with --debug to view the full traceback in logs")
        else:
            lookatme.config.LOG.exception(f"Error rendering slide {number}: {e}")
            click.echo(f"See {log_path} for traceback")
        raise click.Abort()


if __name__ == "__main__":
    main()
