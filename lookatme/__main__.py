#!/usr/bin/env python3

"""
This is the main CLI for lookatme
"""


import io
import logging
import os
import tempfile
import traceback
from typing import Dict, Optional, List

import click

import lookatme
import lookatme.config
import lookatme.log
import lookatme.tui
import lookatme.tutorial
from lookatme.pres import Presentation, DEFAULT_HTML_OPTIONS
from lookatme.schemas import StyleSchema


TO_HTML_DEFAULT_VALUE = "USE_THE_SLIDE_SOURCE_WITH_HTML_EXTENSION"


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
    "--to-html",
    "html_output_dir",
    metavar="OUTPUT_DIR",
    is_flag=False,
    flag_value=TO_HTML_DEFAULT_VALUE,
    help="Render the provided slide source to OUTPUT_DIR. Using this as a"
    " flag wil modify the input file name to be the directory name "
    "(slides.md -> slides_html)",
    required=False,
)
@click.option(
    "--html-option",
    "html_options",
    metavar="HTML_OPTION",
    required=False,
    help=(
        "Provide a specific option to the html rendered with "
        "'--html-option key=value'. Available options are: {option_keys}"
    ).format(option_keys=", ".join(DEFAULT_HTML_OPTIONS.keys())),
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
    html_output_dir: Optional[str],
    html_options: List[str],
):
    """lookatme - An interactive, terminal-based markdown presentation tool.

    See https://lookatme.readthedocs.io/en/v3.0.0rc1 for documentation
    """
    lookatme.config.LOG = lookatme.log.create_log(log_path)
    if debug:
        lookatme.config.LOG.setLevel(logging.DEBUG)
    else:
        lookatme.config.LOG.setLevel(logging.ERROR)

    if len(input_files) == 0:
        input_files = [io.StringIO("")]

    if tutorial:
        if tutorial == "all":
            tutors = ["general", "markdown block", "markdown inline"]
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

    if html_output_dir == TO_HTML_DEFAULT_VALUE:
        input_name = getattr(input_files[0], "name", "slides.md")
        html_output_dir = os.path.splitext(input_name)[0] + "_html"

    if html_output_dir is not None:
        if not os.path.exists(html_output_dir):
            try:
                os.makedirs(html_output_dir)
            except Exception as e:
                lookatme.config.get_log().error(
                    "Could not create output directory: {}".format(e)
                )
                return 1

        if not os.path.isdir(html_output_dir):
            lookatme.config.get_log().error(
                "Html output path is not a directory! {!r}".format(html_output_dir)
            )

        parsed_options = _parse_html_options(html_options, DEFAULT_HTML_OPTIONS)
        pres.to_html(html_output_dir, options=parsed_options)
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


def _parse_html_options(options: List[str], default: Dict):
    res = {}
    for option_str in options:
        parts = [x.strip() for x in option_str.split("=", 1)]
        if len(parts) != 2:
            continue
        key, val = parts
        if key not in default:
            continue
        if isinstance(default[key], int):
            val = int(val)
        res[key] = val
    return res


if __name__ == "__main__":
    main()
