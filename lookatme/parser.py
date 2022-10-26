"""
This module defines the parser for the markdown presentation file
"""


import re
from collections import defaultdict
from typing import AnyStr, Callable, Dict, List, Tuple

import mistune

from lookatme.schemas import MetaSchema
from lookatme.slide import Slide
from lookatme.tutorial import tutor


def is_progressive_slide_delimiter_token(token):
    """Returns True if the token indicates the end of a progressive slide

    :param dict token: The markdown token
    :returns: True if the token is a progressive slide delimiter
    """
    return token["type"] == "close_html" and re.match(r'<!--\s*stop\s*-->', token["text"])


class Parser(object):
    """A parser for markdown presentation files
    """

    def __init__(self, single_slide=False):
        """Create a new Parser instance
        """
        self._single_slide = single_slide

    def parse(self, input_data):
        """Parse the provided input data into a Presentation object

        :param str input_data: The input markdown presentation to parse
        :returns: Presentation
        """
        input_data, meta = self.parse_meta(input_data)
        input_data, slides = self.parse_slides(meta, input_data)
        return meta, slides

    def parse_slides(self, meta, input_data):
        """Parse the Slide out of the input data

        :param dict meta: The parsed meta values
        :param str input_data: The input data string
        :returns: tuple of (remaining_data, slide)
        """
        # slides are delimited by ---
        md = mistune.Markdown()

        state = {}
        tokens = md.block.parse(input_data, state)

        num_hrules, hinfo = self._scan_for_smart_split(tokens)
        keep_split_token = True

        if self._single_slide:
            def slide_split_check(_):  # type: ignore
                return False

            def heading_mod(_):  # type: ignore
                pass
        elif num_hrules == 0:
            if meta.get("title", "") in ["", None]:
                meta["title"] = hinfo["title"]

            def slide_split_check(token):  # type: ignore
                nonlocal hinfo
                return (
                    token["type"] == "heading"
                    and token["level"] == hinfo["lowest_non_title"]
                )

            def heading_mod(token):  # type: ignore
                nonlocal hinfo
                token["level"] = max(
                    token["level"] - (hinfo["title_level"] or 0),
                    1,
                )
            keep_split_token = True
        else:
            def slide_split_check(token):  # type: ignore
                return token["type"] == "hrule"

            def heading_mod(_):  # type: ignore
                pass
            keep_split_token = False

        slides = self._split_tokens_into_slides(
            tokens, slide_split_check, heading_mod, keep_split_token)

        return "", slides

    def _split_tokens_into_slides(
            self,
            tokens: List[Dict],
            slide_split_check: Callable,
            heading_mod: Callable,
            keep_split_token: bool
    ) -> List[Slide]:
        """Split the provided tokens into slides using the slide_split_check
        and heading_mod arguments.
        """
        slides = []
        curr_slide_tokens = []
        for token in tokens:
            should_split = slide_split_check(token)
            if token["type"] == "heading":
                heading_mod(token)

            # new slide!
            if should_split:
                if keep_split_token and len(slides) == 0 and len(curr_slide_tokens) == 0:
                    pass
                else:
                    slides.extend(self._create_slides(
                        curr_slide_tokens, len(slides)))
                curr_slide_tokens = []
                if keep_split_token:
                    curr_slide_tokens.append(token)
                continue
            else:
                curr_slide_tokens.append(token)

        slides.extend(self._create_slides(curr_slide_tokens, len(slides)))

        return slides

    @tutor(
        "general",
        "slides splitting",
        r"""
        Slides can be:

        ## Separated by horizontal rules (three or more `*`, `-`, or `_`)

        ```markdown
        slide 1
        ***
        slide 2
        ```

        ## Split using existing headings ("smart" splitting)

        ```markdown
        # Slide 1

        # Slide 2
        ```

        ## Rendered as a single slide with the `--single` or `--one` CLI parameter

        ```bash
        lookatme --single content.md
        ```
        """,
        order=2,
    )
    def _scan_for_smart_split(self, tokens):
        """Scan the provided tokens for the number of hrules, and the lowest
        (h1 < h2) header level.

        :returns: tuple (num_hrules, lowest_header_level)
        """
        hinfo = {
            "title_level": None,
            "lowest_non_title": 10,
            "counts": defaultdict(int),
            "title": "",
        }
        num_hrules = 0
        first_heading = None
        for token in tokens:
            if token["type"] == "hrule":
                num_hrules += 1
            elif token["type"] == "heading":
                hinfo["counts"][token["level"]] += 1
                if first_heading is None:
                    first_heading = token

        # started off with the lowest heading, make this title
        if (
            hinfo["counts"]
            and first_heading
            and hinfo["counts"][first_heading["level"]] == 1
        ):
            hinfo["title"] = first_heading["text"]
            del hinfo["counts"][first_heading["level"]]
            hinfo["title_level"] = first_heading["level"]

        low_level = min(list(hinfo["counts"].keys()) + [10])
        hinfo["title_level"] = low_level - 1
        hinfo["lowest_non_title"] = low_level

        return num_hrules, hinfo

    @tutor(
        "general",
        "metadata",
        r"""
        The YAML metadata that can be prefixed in slides includes these top level
        fields:

        ```yaml
        ---
        title: "title"
        date: "date"
        author: "author"
        extensions:
          - extension 1
          # .. list of extensions
        styles:
          # .. nested style fields ..
        ---
        ```

        > **NOTE** The `styles` field will be explained in detail with each markdown
        > element.
        """,
        order=3,
    )
    def parse_meta(self, input_data) -> Tuple[AnyStr, Dict]:
        """Parse the PresentationMeta out of the input data

        :param str input_data: The input data string
        :returns: tuple of (remaining_data, meta)
        """
        found_first = False
        yaml_data = []
        skipped_chars = 0
        for line in input_data.split("\n"):
            skipped_chars += len(line) + 1
            stripped_line = line.strip()

            is_marker = (re.match(r'----*', stripped_line) is not None)
            if is_marker:
                if not found_first:
                    found_first = True
                # found the second one
                else:
                    break

            if found_first and not is_marker:
                yaml_data.append(line)
                continue

            # there was no ----* marker
            if not found_first and stripped_line != "":
                break

        if not found_first:
            return input_data, MetaSchema().load_partial_styles({}, partial=True)

        new_input = input_data[skipped_chars:]
        if len(yaml_data) == 0:
            return new_input, MetaSchema().load_partial_styles({}, partial=True)

        yaml_data = "\n".join(yaml_data)
        data = MetaSchema().loads_partial_styles(yaml_data, partial=True)
        return new_input, data

    @tutor(
        "general",
        "progressive slides",
        r"""
        Slides can be progressively displayed by inserting `<!-- stop -->`
        comments between block elemtents (as in, inline within some other
        markdown element).

        <TUTOR:EXAMPLE>
        This will display first, and after you press advance ...

        <!-- stop -->

        This will display!
        </TUTOR:EXAMPLE>
        """,
        order=2,
    )
    def _create_slides(self, tokens, number):
        """Iterate on tokens and create slides out of them. Can create multiple
        slides if the tokens contain progressive slide delimiters.

        :param list tokens: The tokens to create slides out of
        :param int number: The starting slide number
        :returns: A list of Slides
        """
        slide_tokens = []
        for token in tokens:
            if is_progressive_slide_delimiter_token(token):
                yield Slide(slide_tokens[:], number)
                number += 1
            else:
                slide_tokens.append(token)
        yield Slide(slide_tokens, number)
