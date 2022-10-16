"""
Defines all schemas used in lookatme
"""


import datetime
from typing import Dict

import pygments.styles
import yaml
from marshmallow import INCLUDE, RAISE, Schema, fields, validate


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
        if 'yaml_implicit_resolvers' not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
            ]


NoDatesSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')


class YamlRender:
    @staticmethod
    def loads(data): return yaml.load(data, Loader=NoDatesSafeLoader)
    @staticmethod
    def dumps(data): return yaml.safe_dump(data, allow_unicode=True)


class BulletsSchema(Schema):
    default = fields.Str(dump_default="•")

    class Meta:
        include = {
            "1": fields.Str(dump_default="•"),
            "2": fields.Str(dump_default="⁃"),
            "3": fields.Str(dump_default="◦"),
            "4": fields.Str(dump_default="•"),
            "5": fields.Str(dump_default="⁃"),
            "6": fields.Str(dump_default="◦"),
            "7": fields.Str(dump_default="•"),
            "8": fields.Str(dump_default="⁃"),
            "9": fields.Str(dump_default="◦"),
            "10": fields.Str(dump_default="•"),
        }


_NUMBERING_VALIDATION = validate.OneOf(["numeric", "alpha", "roman"])


class NumberingSchema(Schema):
    default = fields.Str(dump_default="numeric",
                         validate=_NUMBERING_VALIDATION)

    class Meta:
        include = {
            "1": fields.Str(dump_default="numeric", validate=_NUMBERING_VALIDATION),
            "2": fields.Str(dump_default="alpha", validate=_NUMBERING_VALIDATION),
            "3": fields.Str(dump_default="roman", validate=_NUMBERING_VALIDATION),
            "4": fields.Str(dump_default="numeric", validate=_NUMBERING_VALIDATION),
            "5": fields.Str(dump_default="alpha", validate=_NUMBERING_VALIDATION),
            "6": fields.Str(dump_default="roman", validate=_NUMBERING_VALIDATION),
            "7": fields.Str(dump_default="numeric", validate=_NUMBERING_VALIDATION),
            "8": fields.Str(dump_default="alpha", validate=_NUMBERING_VALIDATION),
            "9": fields.Str(dump_default="roman", validate=_NUMBERING_VALIDATION),
            "10": fields.Str(dump_default="numeric", validate=_NUMBERING_VALIDATION),
        }


class StyleFieldSchema(Schema):
    fg = fields.Str(dump_default="")
    bg = fields.Str(dump_default="")


class SpacingSchema(Schema):
    top = fields.Int(dump_default=0)
    bottom = fields.Int(dump_default=0)
    left = fields.Int(dump_default=0)
    right = fields.Int(dump_default=0)


class HeadingStyleSchema(Schema):
    prefix = fields.Str()
    suffix = fields.Str()
    fg = fields.Str(dump_default="")
    bg = fields.Str(dump_default="")


class HruleSchema(Schema):
    char = fields.Str(dump_default="─")
    style = fields.Nested(StyleFieldSchema, dump_default=StyleFieldSchema().dump({
        "fg": "#777",
        "bg": "default",
    }))


class BlockQuoteSchema(Schema):
    side = fields.Str(dump_default="╎")
    top_corner = fields.Str(dump_default="┌")
    bottom_corner = fields.Str(dump_default="└")
    style = fields.Nested(StyleFieldSchema, dump_default=StyleFieldSchema().dump({
        "fg": "italics,#aaa",
        "bg": "default",
    }))


class HeadingsSchema(Schema):
    default = fields.Nested(HeadingStyleSchema, dump_default={
        "fg": "#346,bold",
        "bg": "default",
        "prefix": "░░░░░ ",
        "suffix": "",
    })

    class Meta:
        include = {
            "1": fields.Nested(HeadingStyleSchema, dump_default={
                "fg": "#9fc,bold",
                "bg": "default",
                "prefix": "██ ",
                "suffix": "",
            }),
            "2": fields.Nested(HeadingStyleSchema, dump_default={
                "fg": "#1cc,bold",
                "bg": "default",
                "prefix": "▓▓▓ ",
                "suffix": "",
            }),
            "3": fields.Nested(HeadingStyleSchema, dump_default={
                "fg": "#29c,bold",
                "bg": "default",
                "prefix": "▒▒▒▒ ",
                "suffix": "",
            }),
            "4": fields.Nested(HeadingStyleSchema, dump_default={
                "fg": "#559,bold",
                "bg": "default",
                "prefix": "░░░░░ ",
                "suffix": "",
            }),
            "5": fields.Nested(HeadingStyleSchema),
            "6": fields.Nested(HeadingStyleSchema),
        }


class TableSchema(Schema):
    header_divider = fields.Str(dump_default="─")
    column_spacing = fields.Int(dump_default=3)


class StyleSchema(Schema):
    """Styles schema for themes and style overrides within presentations
    """
    class Meta:
        render_module = YamlRender
        unknown = RAISE

    style = fields.Str(
        dump_default="monokai",
        validate=validate.OneOf(list(pygments.styles.get_all_styles())),
    )

    title = fields.Nested(StyleFieldSchema, dump_default={
        "fg": "#f30,bold,italics",
        "bg": "default",
    })
    author = fields.Nested(StyleFieldSchema, dump_default={
        "fg": "#f30",
        "bg": "default",
    })
    date = fields.Nested(StyleFieldSchema, dump_default={
        "fg": "#777",
        "bg": "default",
    })
    slides = fields.Nested(StyleFieldSchema, dump_default={
        "fg": "#f30",
        "bg": "default",
    })
    margin = fields.Nested(SpacingSchema, dump_default={
        "top": 0,
        "bottom": 0,
        "left": 2,
        "right": 2,
    })
    padding = fields.Nested(SpacingSchema, dump_default={
        "top": 0,
        "bottom": 0,
        "left": 10,
        "right": 10,
    })

    headings = fields.Nested(
        HeadingsSchema, dump_default=HeadingsSchema().dump(None))
    bullets = fields.Nested(
        BulletsSchema, dump_default=BulletsSchema().dump(None))
    numbering = fields.Nested(
        NumberingSchema, dump_default=NumberingSchema().dump(None))
    table = fields.Nested(TableSchema, dump_default=TableSchema().dump(None))
    quote = fields.Nested(
        BlockQuoteSchema, dump_default=BlockQuoteSchema().dump(None))
    hrule = fields.Nested(HruleSchema, dump_default=HruleSchema().dump(None))
    link = fields.Nested(StyleFieldSchema, dump_default={
        "fg": "#33c,underline",
        "bg": "default",
    })


class MetaSchema(Schema):
    """The schema for presentation metadata
    """
    class Meta:
        render_module = YamlRender
        unknown = INCLUDE

    title = fields.Str(dump_default="", load_default="")
    date = fields.Str(
        dump_default=datetime.datetime.now().strftime("%Y-%m-%d"),
        load_default=datetime.datetime.now().strftime("%Y-%m-%d"),
    )
    author = fields.Str(dump_default="", load_default="")
    styles = fields.Nested(
        StyleSchema,
        dump_default=StyleSchema().dump(None),
        load_default=StyleSchema().dump(None),
    )
    extensions = fields.List(fields.Str(), dump_default=[], load_default=[])

    def _ensure_top_level_defaults(self, res: Dict) -> Dict:
        res.setdefault("title", "")
        res.setdefault("author", "")
        res.setdefault("date", datetime.datetime.now().strftime("%Y-%m-%d"))
        res.setdefault("extensions", [])

        return res

    def loads_partial_styles(self, *args, **kwargs):
        kwargs["partial"] = True
        res = super(self.__class__, self).loads(*args, **kwargs)
        if res is None:
            raise ValueError("Could not loads")

        res = self._ensure_top_level_defaults(res)
        return res

    def loads(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).loads(*args, **kwargs)
        if res is None:
            raise ValueError("Could not loads")

        return res

    def load_partial_styles(self, *args, **kwargs):
        kwargs["partial"] = True
        res = super(self.__class__, self).load(*args, **kwargs)
        if res is None:
            raise ValueError("Could not loads")

        res = self._ensure_top_level_defaults(res)
        return res

    def load(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).load(*args, **kwargs)
        if res is None:
            raise ValueError("Could not load")

        return res

    def dump(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).dump(*args, **kwargs)
        if res is None:
            raise ValueError("Could not dump")
        return res
