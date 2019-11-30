"""
This module defines the parser for the markdown presentation file
"""


from marshmallow import fields, Schema
import mistune
import re
import yaml


from lookatme.schemas import MetaSchema
from lookatme.slide import Slide


class Parser(object):
    """A parser for markdown presentation files
    """

    def __init__(self):
        """Create a new Parser instance
        """

    def parse(self, input_data):
        """Parse the provided input data into a Presentation object

        :param str input_data: The input markdown presentation to parse
        :returns: Presentation
        """
        input_data, meta = self.parse_meta(input_data)
        input_data, slides = self.parse_slides(input_data)
        return meta, slides
    
    def parse_slides(self, input_data):
        """Parse the Slide out of the input data

        :param str input_data: The input data string
        :returns: tuple of (remaining_data, slide)
        """
        # slides are delimited by ---
        md = mistune.Markdown()

        state = {}
        tokens = md.block.parse(input_data, state)

        slides = []
        curr_slide_tokens = []
        for token in tokens:
            # new slide!
            if token["type"] == "hrule":
                slide = Slide(curr_slide_tokens, md, len(slides))
                slides.append(slide)
                curr_slide_tokens = []
                continue
            else:
                curr_slide_tokens.append(token)

        slides.append(Slide(curr_slide_tokens, md, len(slides)))

        return "", slides
    
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
