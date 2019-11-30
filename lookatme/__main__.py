#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import click
import logging
import os
import pygments.styles
import sys


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
    default="/tmp/lookatme.log",
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
@click.argument("input_file", type=click.File(), default=sys.stdin)
def main(debug, log_path, theme, code_style, dump_styles, input_file, live_reload):
    """lookatme - An interactive, terminal-based markdown presentation tool.
    """
    if debug:
        lookatme.config.LOG = lookatme.log.create_log(log_path)
    else:
        lookatme.config.LOG = lookatme.log.create_null_log()

    pres = Presentation(input_file, theme, code_style, live_reload=live_reload)

    if dump_styles:
        print(StyleSchema().dumps(pres.styles))
        return 0

    pres.run()


if __name__ == "__main__":
    main()
