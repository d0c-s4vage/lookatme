"""
Defines all schemas used in lookatme
"""

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
    dumps = lambda data: yaml.safe_dump(data)


class BulletsSchema(Schema):
    default = fields.Str(required=True, default="•")

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


class TableSchema(Schema):
    header_divider = fields.Str(default="─")
    column_spacing = fields.Int(default=3)


class StyleFieldSchema(Schema):
    fg = fields.Str(default="")
    bg = fields.Str(default="")


class StyleSchema(Schema):
    """Styles schema for themes and style overrides within presentations
    """
    class Meta:
        render_module = YamlRender

    style = fields.Str(
        default="monokai",
        validate=validate.OneOf(list(pygments.styles.get_all_styles())),
    )
    bullets = fields.Nested(BulletsSchema, default=BulletsSchema().dump(BulletsSchema()))
    table = fields.Nested(TableSchema, default=TableSchema().dump(TableSchema()))
    quote_style = fields.Nested(StyleFieldSchema, default=StyleFieldSchema().dump({
        "fg": "italics,#aaa",
        "bg": "default",
    }))


class MetaSchema(Schema):
    """The schema for presentation metadata
    """
    class Meta:
        render_module = YamlRender

    title = fields.Str()
    date = fields.Date()
    author = fields.Str()
    styles = fields.Nested(StyleSchema, default={})
    extensions = fields.List(fields.Str(), default=[])
