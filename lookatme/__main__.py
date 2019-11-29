#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import click
import logging
import os
import sys


from lookatme.parser import Parser
import lookatme.tui
import lookatme.log
import lookatme.config


@click.command()
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
    "style",
    type=click.Choice(["dark", "light"]),
    default="dark",
)
@click.argument("input_file", type=click.File(), default=sys.stdin)
def main(debug, log_path, style, input_file):
    """Main
    """
    if debug:
        lookatme.config.LOG = lookatme.log.create_log(log_path)
    else:
        lookatme.config.LOG = lookatme.log.create_null_log()

    style_mod = __import__("lookatme.styles." + style, fromlist=[style])
    lookatme.config.STYLE = style_mod

    data = input_file.read()
    parser = Parser()
    pres = parser.parse(data)
    lookatme.tui.run_presentation(pres)


if __name__ == "__main__":
    main()
