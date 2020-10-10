"""
Defines all schemas used in lookatme
"""


import datetime
from marshmallow import Schema, fields, validate
import pygments.styles
import yaml


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


class YamlRender:
    loads = lambda data: yaml.load(data, Loader=NoDatesSafeLoader)
    dumps = lambda data: yaml.safe_dump(data, allow_unicode=True)


class BulletsSchema(Schema):
    default = fields.Str(default="•")

    class Meta:
        include = {
            "1": fields.Str(default="•"),
            "2": fields.Str(default="⁃"),
            "3": fields.Str(default="◦"),
            "4": fields.Str(),
            "5": fields.Str(),
            "6": fields.Str(),
            "7": fields.Str(),
            "8": fields.Str(),
            "9": fields.Str(),
            "10": fields.Str(),
        }

_NUMBERING_VALIDATION = validate.OneOf(["numeric", "alpha", "roman"])
class NumberingSchema(Schema):
    default = fields.Str(default="numeric", validate=_NUMBERING_VALIDATION)

    class Meta:
        include = {
            "1": fields.Str(default="numeric", validate=_NUMBERING_VALIDATION),
            "2": fields.Str(default="alpha", validate=_NUMBERING_VALIDATION),
            "3": fields.Str(default="roman", validate=_NUMBERING_VALIDATION),
            "4": fields.Str(validate=_NUMBERING_VALIDATION),
            "5": fields.Str(validate=_NUMBERING_VALIDATION),
            "6": fields.Str(validate=_NUMBERING_VALIDATION),
            "7": fields.Str(validate=_NUMBERING_VALIDATION),
            "8": fields.Str(validate=_NUMBERING_VALIDATION),
            "9": fields.Str(validate=_NUMBERING_VALIDATION),
            "10": fields.Str(validate=_NUMBERING_VALIDATION),
        }


class StyleFieldSchema(Schema):
    fg = fields.Str(default="")
    bg = fields.Str(default="")


class SpacingSchema(Schema):
    top = fields.Int(default=0)
    bottom = fields.Int(default=0)
    left = fields.Int(default=0)
    right = fields.Int(default=0)


class HeadingStyleSchema(Schema):
    prefix = fields.Str()
    suffix = fields.Str()
    fg = fields.Str(default="")
    bg = fields.Str(default="")


class HruleSchema(Schema):
    char = fields.Str(default="─")
    style = fields.Nested(StyleFieldSchema, default=StyleFieldSchema().dump({
        "fg": "#777",
        "bg": "default",
    }))


class BlockQuoteSchema(Schema):
    side = fields.Str(default="╎")
    top_corner = fields.Str(default="┌")
    bottom_corner = fields.Str(default="└")
    style = fields.Nested(StyleFieldSchema, default=StyleFieldSchema().dump({
        "fg": "italics,#aaa",
        "bg": "default",
    }))


class HeadingsSchema(Schema):
    default = fields.Nested(HeadingStyleSchema, default={
        "fg": "#346,bold",
        "bg": "default",
        "prefix": "░░░░░ ",
        "suffix": "",
    })

    class Meta:
        include = {
            "1": fields.Nested(HeadingStyleSchema, default={
                "fg": "#9fc,bold",
                "bg": "default",
                "prefix": "██ ",
                "suffix": "",
            }),
            "2": fields.Nested(HeadingStyleSchema, default={
                "fg": "#1cc,bold",
                "bg": "default",
                "prefix": "▓▓▓ ",
                "suffix": "",
            }),
            "3": fields.Nested(HeadingStyleSchema, default={
                "fg": "#29c,bold",
                "bg": "default",
                "prefix": "▒▒▒▒ ",
                "suffix": "",
            }),
            "4": fields.Nested(HeadingStyleSchema, default={
                "fg": "#559,bold",
                "bg": "default",
                "prefix": "░░░░░ ",
                "suffix": "",
            }),
            "5": fields.Nested(HeadingStyleSchema),
            "6": fields.Nested(HeadingStyleSchema),
        }


class TableSchema(Schema):
    header_divider = fields.Str(default="─")
    column_spacing = fields.Int(default=3)


class StyleSchema(Schema):
    """Styles schema for themes and style overrides within presentations
    """
    class Meta:
        render_module = YamlRender

    style = fields.Str(
        default="monokai",
        validate=validate.OneOf(list(pygments.styles.get_all_styles())),
    )

    title = fields.Nested(StyleFieldSchema, default={
        "fg": "#f30,bold,italics",
        "bg": "default",
    })
    author = fields.Nested(StyleFieldSchema, default={
        "fg": "#f30",
        "bg": "default",
    })
    date = fields.Nested(StyleFieldSchema, default={
        "fg": "#777",
        "bg": "default",
    })
    slides = fields.Nested(StyleFieldSchema, default={
        "fg": "#f30",
        "bg": "default",
    })
    margin = fields.Nested(SpacingSchema, default={
        "top": 0,
        "bottom": 0,
        "left": 2,
        "right": 2,
    })
    padding = fields.Nested(SpacingSchema, default={
        "top": 0,
        "bottom": 0,
        "left": 10,
        "right": 10,
    })

    headings = fields.Nested(HeadingsSchema, default=HeadingsSchema().dump(HeadingsSchema()))
    bullets = fields.Nested(BulletsSchema, default=BulletsSchema().dump(BulletsSchema()))
    numbering = fields.Nested(NumberingSchema, default=NumberingSchema().dump(NumberingSchema()))
    table = fields.Nested(TableSchema, default=TableSchema().dump(TableSchema()))
    quote = fields.Nested(BlockQuoteSchema, default=BlockQuoteSchema().dump(BlockQuoteSchema()))
    hrule = fields.Nested(HruleSchema, default=HruleSchema().dump(HruleSchema()))
    link = fields.Nested(StyleFieldSchema, default={
        "fg": "#33c,underline",
        "bg": "default",
    })


class MetaSchema(Schema):
    """The schema for presentation metadata
    """
    class Meta:
        render_module = YamlRender

    title = fields.Str(default="", missing="")
    date = fields.Date(
        default=datetime.datetime.now(),
        missing=datetime.datetime.now(),
    )
    author = fields.Str(default="", missing="")
    styles = fields.Nested(StyleSchema, default={}, missing={})
    extensions = fields.List(fields.Str(), default=[], missing={})
