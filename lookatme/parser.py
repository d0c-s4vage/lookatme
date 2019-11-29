"""
This module defines the parser for the markdown presentation file
"""


from marshmallow import fields, Schema
import mistune
import re
import yaml


from lookatme.pres import PresentationMeta, Presentation, Slide


class NoDatesSafeLoader(yaml.SafeLoader):
    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove):
        """
        Remove implicit resolvers for a particular tag

        Takes care not to modify resolvers in super classes.

        We want to load datetimes as strings, not dates, because we
        go on to serialise as json which doesn't have the advanced types
        of yaml, and leads to incompatibilities down the track.
        """
        if not 'yaml_implicit_resolvers' in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
            ]
NoDatesSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')


render_module = type(
    "render_module",
    (object,),
    {
        "loads": lambda self, data: yaml.load(data, Loader=NoDatesSafeLoader),
        "dumps": lambda self, data: yaml.dumps(data),
    },
)()


class MetaSchema(Schema):
    """The schema for presentation metadata
    """
    class Meta:
        render_module = render_module

    title = fields.Str()
    date = fields.Date()
    author = fields.Str()


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
        return Presentation(meta, slides)
    
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
            return input_data, PresentationMeta()
        
        new_input = input_data[skipped_chars:]
        if len(yaml_data) == 0:
            return new_input, PresentationMeta()

        yaml_data = "\n".join(yaml_data)
        data = MetaSchema().loads(yaml_data)
        meta = PresentationMeta(**data)

        return new_input, meta
