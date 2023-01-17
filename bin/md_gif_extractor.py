#!/usr/bin/env python

import click
import inspect
import tempfile


from lookatme.parser import md_to_tokens
from lookatme.pres import Presentation
from lookatme.render.markdown_block import parse_fence_info
import lookatme.output


@click.command(help=inspect.cleandoc(r"""
    Create a gif from specially marked markdown code blocks. The markdown code
    blocks (specifically, fenced code) should be marked with the extra metadata
    like so: ```markdown {gif=true gif.rows=30 ...other gif options...}
""").strip())
@click.option(
    "-i",
    "--input",
    "input_stream",
    help="Input stream to read from",
    type=click.File("r")
)
@click.option(
    "-o",
    "--output",
    "output_stream",
    help="Output stream to write to",
    type=click.File("wb"),
)
def main(input_stream, output_stream):
    for token in md_to_tokens(input_stream.read()):
        if token["type"] != "fence":
            continue
        
        info = token.get("info", "")
        fence_info = parse_fence_info(info)
        if fence_info.lang.lower() not in ("markdown", "md"):
            continue
        if fence_info.raw_attrs.get("gif", "").lower() not in ("true", "yes", "1"):
            continue

        md_to_render = token["content"]
        pres = Presentation(input_str=md_to_render)

        gif_options = lookatme.output.parse_options(fence_info.raw_curly.split())

        with tempfile.NamedTemporaryFile(prefix="lookatme-") as f:
            lookatme.output.output_pres(pres, f.name, "gif", gif_options)

            gif_data = f.read()

        output_stream.write(gif_data)


if __name__ == "__main__":
    main()
