"""
This module defines the parser for the markdown presentation file
"""


import re
from collections import defaultdict
import copy
from typing import cast, AnyStr, Callable, Dict, List, Tuple

import markdown_it
import markdown_it.token

from lookatme.schemas import MetaSchema
from lookatme.slide import Slide
from lookatme.tutorial import tutor
import lookatme.utils as utils


def _set_map_for_inline(token: Dict):
    start = token["map"][0]
    for child in token["children"]:
        child["map"] = [start, start + 1]
        if child["type"] == "softbreak":
            start += 1


def md_to_tokens(md_text):
    md = markdown_it.MarkdownIt("gfm-like").disable("html_block")
    tokens = md.parse(md_text)
    res = []
    for token_tmp in tokens:
        token = cast(Dict, token_tmp.as_dict())
        if token["type"] in ("heading_open", "heading_close"):
            token["level"] = int(token["tag"].replace("h", ""))
        if token["type"] == "inline":
            _set_map_for_inline(token)
        res.append(token)

    return res


def is_heading(token):
    return token["type"] == "heading_open"


def is_hrule(token):
    return token["type"] == "hr"


class SlideIsolator:
    def __init__(self):
        self.slide_tokens = []
        self.slides = []
        self.number = 0

    def create_slides(self, tokens, number) -> List[Slide]:
        self.slide_tokens = []
        self.slides: List[Slide] = []
        self.number = number

        self._isolate_progressive_slides(tokens, self.slide_tokens)

        if not self.slides or (
            self.slides and self.slides[-1].tokens != self.slide_tokens
        ):
            self._isolate_slide()

        return self.slides

    def _is_progressive_slide_delimiter(self, token: Dict) -> bool:
        return (
            token["type"] == "html_inline"
            and re.match(r"<!--\s*stop\s*-->", token["content"]) is not None
        )

    def _isolate_progressive_slides(
        self,
        input_tokens: List[Dict],
        output_tokens: List[Dict],
    ):
        """Recursively iterate through the provided input tokens, calling the
        isolate_slide callback whenever a progressive slide token is found. Also
        adding all iterated tokens back into the output_tokens list.
        """
        for token in input_tokens:
            if self._is_progressive_slide_delimiter(token):
                self._isolate_slide()
                continue

            children = token.get("children", None)
            if children is not None:
                # shallow copy here is fine - we only care about zeroing out the
                # children and adding the children back in one-by-one
                output_token = copy.copy(token)
                output_token["children"] = []
                output_tokens.append(output_token)
                self._isolate_progressive_slides(
                    children,
                    output_token["children"],
                )
            else:
                output_tokens.append(token)

    def _isolate_slide(self):
        self.slides.append(Slide(copy.deepcopy(self.slide_tokens), self.number))
        self.number += 1


class Parser(object):
    """A parser for markdown presentation files"""

    def __init__(self, single_slide=False):
        """Create a new Parser instance"""
        self._single_slide = single_slide

    def parse(self, input_data) -> Tuple[Dict, List[Slide], str]:
        """Parse the provided input data into a Presentation object

        :param str input_data: The input markdown presentation to parse
        """
        no_meta_input_data, meta = self.parse_meta(input_data)
        slides = self.parse_slides(meta, no_meta_input_data)
        return meta, slides, no_meta_input_data

    def parse_slides(self, meta, input_data) -> List[Slide]:
        """Parse the Slide out of the input data

        :param dict meta: The parsed meta values
        :param str input_data: The input data string
        :returns: List[Slide]
        """
        tokens = md_to_tokens(input_data)
        utils.debug_print_tokens(tokens)
        num_hrules, hinfo = self._scan_for_smart_split(tokens)
        keep_split_token = True

        if self._single_slide:
            return [Slide(tokens, 0)]

        if num_hrules == 0:
            if meta.get("title", "") in ["", None]:
                meta["title"] = hinfo["title"]

            def slide_split_check(token):  # type: ignore
                nonlocal hinfo
                return is_heading(token) and token["level"] == hinfo["lowest_non_title"]

            def heading_mod(token):  # type: ignore
                nonlocal hinfo
                token["level"] = max(
                    token["level"] - (hinfo["title_level"] or 0),
                    1,
                )

            keep_split_token = True
        else:

            def slide_split_check(token):  # type: ignore
                return is_hrule(token)

            def heading_mod(_):  # type: ignore
                pass

            keep_split_token = False

        slides = self._split_tokens_into_slides(
            tokens, slide_split_check, heading_mod, keep_split_token
        )

        return slides

    def _split_tokens_into_slides(
        self,
        tokens: List[Dict],
        slide_split_check: Callable,
        heading_mod: Callable,
        keep_split_token: bool,
    ) -> List[Slide]:
        """Split the provided tokens into slides using the slide_split_check
        and heading_mod arguments.
        """
        slides = []
        curr_slide_tokens = []
        for token in tokens:
            should_split = slide_split_check(token)
            if is_heading(token):
                heading_mod(token)

            # new slide!
            if should_split:
                if (
                    keep_split_token
                    and len(slides) == 0
                    and len(curr_slide_tokens) == 0
                ):
                    pass
                else:
                    slides.extend(self._create_slides(curr_slide_tokens, len(slides)))
                curr_slide_tokens = []
                if keep_split_token:
                    curr_slide_tokens.append(token)
                continue
            else:
                curr_slide_tokens.append(token)

        slides.extend(self._create_slides(curr_slide_tokens, len(slides)))

        return slides

    def _get_heading_contents(self, tokens, start_idx):
        num_heading_opens = 0
        res = []
        for token in tokens[start_idx:]:
            if token["type"] == "heading_open":
                num_heading_opens += 1
            elif token["type"] == "heading_close":
                num_heading_opens -= 1
                if num_heading_opens == 0:
                    break
            else:
                res.append(token)
        return res

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
        first_heading_contents = None
        for idx, token in enumerate(tokens):
            if is_hrule(token):
                num_hrules += 1
            elif is_heading(token):
                hinfo["counts"][token["level"]] += 1
                if first_heading is None:
                    first_heading = token
                    first_heading_contents = self._get_heading_contents(tokens, idx)

        # started off with the lowest heading, make this title
        if (
            hinfo["counts"]
            and first_heading
            and isinstance(first_heading_contents, list)
            and hinfo["counts"][first_heading["level"]] == 1
        ):
            map_start = first_heading_contents[0]["map"]
            map_end = first_heading_contents[-1]["map"]
            hinfo["title"] = (
                [{"type": "paragraph_open", "map": [map_start[0], map_start[0] + 1]}]
                + first_heading_contents
                + [{"type": "paragraph_close", "map": [map_end[-1] - 1, map_end[-1]]}]
            )
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

            is_marker = re.match(r"----*", stripped_line) is not None
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
        comments anywhere in the markdown.

        <TUTOR:EXAMPLE>
        This will display first, and after you press advance ...<!-- stop -->

        * this <!-- stop -->
          * displays <!-- stop -->

        | and <!-- stop --> | then <!-- stop -->     |
        |-------------------|------------------------|
        | this              | and this               |

        <!-- stop -->

        and finally this!
        </TUTOR:EXAMPLE>
        """,
        order=2,
    )
    def _create_slides(self, tokens, number):
        """Create additional slides from the provided token stream, splitting
        wherever progressive slide markers are found.
        """
        slide_isolator = SlideIsolator()
        return slide_isolator.create_slides(tokens, number)
