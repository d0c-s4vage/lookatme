"""
This module defines the parser for the markdown presentation file
"""


from collections import defaultdict
from marshmallow import fields, Schema
import mistune
import re
import yaml


from lookatme.schemas import MetaSchema
from lookatme.slide import Slide


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

        if self._single_slide:
            def slide_split_check(token):
                False
            def heading_mod(token):
                pass
        elif num_hrules == 0:
            if meta["title"] in ["", None]:
                meta["title"] = hinfo["title"]
            def slide_split_check(token):
                return (
                    token["type"] == "heading"
                    and token["level"] == hinfo["lowest_non_title"]
                )
            def heading_mod(token):
                token["level"] = max(
                    token["level"] - (hinfo["title_level"] or 0),
                    1,
                )
            keep_split_token = True
        else:
            def slide_split_check(token):
                return token["type"] == "hrule"
            def heading_mod(token):
                pass
            keep_split_token = False

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
                    slide = Slide(curr_slide_tokens, md, len(slides))
                    slides.append(slide)
                curr_slide_tokens = []
                if keep_split_token:
                    curr_slide_tokens.append(token)
                continue
            else:
                curr_slide_tokens.append(token)

        slides.append(Slide(curr_slide_tokens, md, len(slides)))

        return "", slides

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
        if hinfo["counts"] and hinfo["counts"][first_heading["level"]] == 1:
            hinfo["title"] = first_heading["text"]
            del hinfo["counts"][first_heading["level"]]
            hinfo["title_level"] = first_heading["level"]

        low_level = min(list(hinfo["counts"].keys()) + [10])
        hinfo["title_level"] = low_level - 1
        hinfo["lowest_non_title"] = low_level

        return num_hrules, hinfo
    
    def parse_meta(self, input_data):
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
            return input_data, MetaSchema().load({})
        
        new_input = input_data[skipped_chars:]
        if len(yaml_data) == 0:
            return new_input, MetaSchema().load({})

        yaml_data = "\n".join(yaml_data)
        data = MetaSchema().loads(yaml_data)
        return new_input, data
