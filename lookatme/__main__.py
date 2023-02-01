#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import io
import logging
import os
import tempfile
import traceback
from typing import Optional, List

import click

import lookatme
import lookatme.config
import lookatme.log
import lookatme.tui
import lookatme.tutorial
from lookatme.pres import Presentation
from lookatme.schemas import StyleSchema
import lookatme.output


@click.command("lookatme")
@click.option("--debug", "debug", is_flag=True, default=False)
@click.option("--threads", "threads", is_flag=True, default=False)
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
    ),
)
@click.option(
    "-t",
    "--theme",
    "theme",
    type=click.Choice(["dark", "light"]),
    default=None,
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
    default=False,
)
@click.option(
    "-f",
    "--format",
    "output_format",
    required=False,
    default=None,
    type=click.Choice(lookatme.output.get_all_formats()),
    help="The output format to convert the markdown to. See also --output and "
    f"--opt.{lookatme.output.get_available_to_install_msg()}",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    metavar="OUTPUT_PATH",
    help="Output the markdown slides in a specific --format to this path",
    required=False,
)
@click.option(
    "--opt",
    "output_options",
    metavar="OPTION",
    required=False,
    help=(
        "Provide a specific option for the output format in the form "
        "key=value. Use 'help' or 'list' to see all output options."
    ),
    multiple=True,
)
@click.version_option(lookatme.__version__)
@click.argument(
    "input_files",
    type=click.File("r"),
    nargs=-1,
)
def main(
    tutorial,
    debug,
    threads,
    log_path,
    theme,
    dump_styles,
    input_files,
    live_reload,
    extensions,
    single_slide,
    safe,
    no_ext_warn,
    ignore_ext_failure,
    output_path: Optional[str],
    output_options: List[str],
    output_format: str = "html",
):
    """lookatme - An interactive, terminal-based markdown presentation tool.

    See https://lookatme.readthedocs.io/en/v3.0.0rc4 for documentation
    """
    lookatme.config.LOG = lookatme.log.create_log(log_path)
    if debug:
        lookatme.config.LOG.setLevel(logging.DEBUG)
    else:
        lookatme.config.LOG.setLevel(logging.INFO)

    if len(input_files) == 0:
        input_files = [io.StringIO("")]

    if tutorial:
        if tutorial == "all":
            tutors = ["general", "markdown block", "markdown inline", "output"]
        else:
            tutors = [x.strip() for x in tutorial.split(",")]

        if theme is None:
            theme = "dark"
        theme_mod = __import__("lookatme.themes." + theme, fromlist=[theme])
        lookatme.config.set_global_style_with_precedence(
            theme_mod,
            {},
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
        live_reload=live_reload,
        single_slide=single_slide,
        preload_extensions=preload_exts,
        safe=safe,
        no_ext_warn=no_ext_warn,
        ignore_ext_failure=ignore_ext_failure,
        no_threads=(debug and not threads),
    )

    if dump_styles:
        print(StyleSchema().dumps(pres.styles))
        return 0

    if len(output_options) == 1 and output_options[0] in ("help", "list"):
        print(lookatme.output.get_output_options_help())
        return 1

    if output_path is not None:
        parsed_out_opts = lookatme.output.parse_options(output_options)
        lookatme.output.output_pres(pres, output_path, output_format, parsed_out_opts)
        return 0

    try:
        pres.run()
    except Exception as e:
        number = pres.get_tui().curr_slide.number + 1
        click.echo(f"Error rendering slide {number}: {e}")
        if not debug:
            click.echo(
                "Rerun with --debug to run with no threads and more details in the logs"
            )
            lookatme.config.get_log().error(
                f"Error rendering slide {number}", exc_info=True
            )
        else:
            click.echo(f"Error rendering slide {number}: {e}")
            click.echo("")
            click.echo(
                "\n".join("    " + line for line in traceback.format_exc().split("\n"))
            )
            click.echo(f"See {log_path} for detailed runtime logs")
        raise click.Abort()


if __name__ == "__main__":
    main()
