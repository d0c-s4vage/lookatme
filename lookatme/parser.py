"""
This module defines the parser for the markdown presentation file
"""


import re
from collections import defaultdict
from typing import AnyStr, Callable, Dict, List, Tuple

import markdown_it
import markdown_it.token

import lookatme.config
from lookatme.schemas import MetaSchema
from lookatme.slide import Slide


def md_to_tokens(md_text):
    md = markdown_it.MarkdownIt("gfm-like").disable("html_block")
    tokens = md.parse(md_text)
    res = []
    for token in tokens:
        token = token.as_dict()
        if token["type"] in ("heading_open", "heading_close"):
            token["level"] = int(token["tag"].replace("h", ""))
        res.append(token)

    return res


def is_heading(token):
    return token["type"] == "heading_open"


def is_hrule(token):
    return token["type"] == "hr"


def debug_print_tokens(tokens, level=1):
    """Print the tokens DFS"""

    def indent(x):
        return "  " * x

    log = lookatme.config.get_log()
    log.debug(indent(level) + "DEBUG TOKENS")
    level += 1

    stack = list(reversed(tokens))
    while len(stack) > 0:
        token = stack.pop()
        if "close" in token["type"]:
            level -= 1

        log.debug(indent(level) + repr(token))

        if "open" in token["type"]:
            level += 1

        token_children = token.get("children", None)
        if isinstance(token_children, list):
            stack.append({"type": "children_close"})
            stack += list(reversed(token_children))
            stack.append({"type": "children_open"})


def is_progressive_slide_delimiter_token(token):
    """Returns True if the token indicates the end of a progressive slide

    :param dict token: The markdown token
    :returns: True if the token is a progressive slide delimiter
    """
    return token["type"] == "close_html" and re.match(
        r"<!--\s*stop\s*-->", token["text"]
    )


class Parser(object):
    """A parser for markdown presentation files"""

    def __init__(self, single_slide=False):
        """Create a new Parser instance"""
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
        tokens = md_to_tokens(input_data)
        debug_print_tokens(tokens)
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

            def slide_split_check(token):
                nonlocal hinfo
                return is_heading(token) and token["level"] == hinfo["lowest_non_title"]

            def heading_mod(token):
                nonlocal hinfo
                token["level"] = max(
                    token["level"] - (hinfo["title_level"] or 0),
                    1,
                )

            keep_split_token = True
        else:

            def slide_split_check(token):
                return is_hrule(token)

            def heading_mod(token):
                pass

            keep_split_token = False

        slides = self._split_tokens_into_slides(
            tokens, slide_split_check, heading_mod, keep_split_token
        )

        return "", slides

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
            hinfo["title"] = (
                [{"type": "paragraph_open"}]
                + first_heading_contents
                + [{"type": "paragraph_close"}]
            )
            del hinfo["counts"][first_heading["level"]]
            hinfo["title_level"] = first_heading["level"]

        low_level = min(list(hinfo["counts"].keys()) + [10])
        hinfo["title_level"] = low_level - 1
        hinfo["lowest_non_title"] = low_level

        return num_hrules, hinfo

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
