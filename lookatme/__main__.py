#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import click
import logging
import os
import pygments.styles
import sys


from lookatme.parser import Parser
import lookatme.tui
import lookatme.log
import lookatme.config
import lookatme.themes
from lookatme.schemas import StyleSchema
from lookatme.utils import dict_deep_update


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
@click.argument("input_file", type=click.File(), default=sys.stdin)
def main(debug, log_path, theme, code_style, dump_styles, input_file):
    """lookatme - An interactive, terminal-based markdown presentation tool.
    """
    if debug:
        lookatme.config.LOG = lookatme.log.create_log(log_path)
    else:
        lookatme.config.LOG = lookatme.log.create_null_log()

    theme_mod = __import__("lookatme.themes." + theme, fromlist=[theme])
    styles = lookatme.themes.ensure_defaults(theme_mod)

    data = input_file.read()
    parser = Parser()
    pres = parser.parse(data)

    if pres.meta.styles is not None:
        dict_deep_update(styles, pres.meta.styles)

    # now apply any command-line style overrides
    if code_style is not None:
        styles["style"] = code_style

    if dump_styles:
        print(StyleSchema().dumps(styles))
        return 0

    lookatme.config.STYLE = styles

    lookatme.tui.run_presentation(pres)


if __name__ == "__main__":
    main()
