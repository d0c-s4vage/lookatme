"""
Defines all schemas used in lookatme
"""


import datetime
from typing import cast, Dict

import pygments.styles
import pygments.lexers
import yaml
from marshmallow import INCLUDE, RAISE, Schema, fields, validate


line_color = "#505050"


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
        if "yaml_implicit_resolvers" not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
            ]


NoDatesSafeLoader.remove_implicit_resolver("tag:yaml.org,2002:timestamp")


class YamlRender:
    @staticmethod
    def loads(data):
        return yaml.load(data, Loader=NoDatesSafeLoader)

    @staticmethod
    def dumps(data):
        return yaml.safe_dump(data, allow_unicode=True)


class StyleFieldSchema(Schema):
    fg = fields.Str(dump_default="")
    bg = fields.Str(dump_default="")


class TextStyleFieldSchema(Schema):
    text = fields.Str(dump_default=" ")
    fg = fields.Str(dump_default="")
    bg = fields.Str(dump_default="")


class BulletsSchema(Schema):
    default = fields.Nested(
        TextStyleFieldSchema(),
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "•",
                "fg": "bold",
                "bg": "",
            }
        ),
    )

    class Meta:
        include = {
            "1": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "•",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "2": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "⁃",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "3": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "◦",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "4": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "•",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "5": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "⁃",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "6": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "◦",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
        }


_NUMBERING_VALIDATION = validate.OneOf(["numeric", "alpha", "roman"])


class NumberingSchema(Schema):
    default = fields.Nested(
        TextStyleFieldSchema(),
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "numeric",
                "fg": "bold",
                "bg": "",
            }
        ),
    )

    class Meta:
        include = {
            "1": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "numeric",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "2": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "alpha",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "3": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "roman",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "4": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "numeric",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "5": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "alpha",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
            "6": fields.Nested(
                TextStyleFieldSchema(),
                dump_default=TextStyleFieldSchema().dump(
                    {
                        "text": "roman",
                        "fg": "bold",
                        "bg": "",
                    }
                ),
            ),
        }


class BorderBoxSchema(Schema):
    tl_corner = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "┌",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    t_line = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "─",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    tr_corner = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "┐",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    r_line = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "│",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    br_corner = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "┘",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    b_line = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "─",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    bl_corner = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "└",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    l_line = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "│",
                "fg": "bold",
                "bg": "",
            }
        ),
    )


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


class HruleSchema(TextStyleFieldSchema):
    text = fields.Str(dump_default="─")


class BlockQuoteSchema(Schema):
    style = fields.Nested(
        StyleFieldSchema,
        dump_default=StyleFieldSchema().dump(
            {
                "fg": "italics,#aaa",
                "bg": "default",
            }
        ),
    )
    border = fields.Nested(
        BorderBoxSchema,
        dump_default=BorderBoxSchema().dump(
            {
                "tl_corner": {"text": "╭── ", "fg": line_color},
                "l_line": {"text": "│", "fg": line_color},
                "bl_corner": {"text": "╰── ", "fg": line_color},
                "b_line": {"text": " ", "fg": "", "bg": ""},
                "r_line": {"text": " ", "fg": "", "bg": ""},
                "t_line": {"text": " ", "fg": "", "bg": ""},
                "br_corner": {"text": " ", "fg": "", "bg": ""},
                "tr_corner": {"text": " ", "fg": "", "bg": ""},
            }
        ),
    )


class HeadingsSchema(Schema):
    default = fields.Nested(
        HeadingStyleSchema,
        dump_default={
            "fg": "#346,bold",
            "bg": "default",
            "prefix": "░░░░░ ",
            "suffix": "",
        },
    )

    class Meta:
        include = {
            "1": fields.Nested(
                HeadingStyleSchema,
                dump_default={
                    "fg": "#9fc,bold",
                    "bg": "default",
                    "prefix": "██ ",
                    "suffix": "",
                },
            ),
            "2": fields.Nested(
                HeadingStyleSchema,
                dump_default={
                    "fg": "#1cc,bold",
                    "bg": "default",
                    "prefix": "▓▓▓ ",
                    "suffix": "",
                },
            ),
            "3": fields.Nested(
                HeadingStyleSchema,
                dump_default={
                    "fg": "#29c,bold",
                    "bg": "default",
                    "prefix": "▒▒▒▒ ",
                    "suffix": "",
                },
            ),
            "4": fields.Nested(
                HeadingStyleSchema,
                dump_default={
                    "fg": "#559,bold",
                    "bg": "default",
                    "prefix": "░░░░░ ",
                    "suffix": "",
                },
            ),
            "5": fields.Nested(HeadingStyleSchema),
            "6": fields.Nested(HeadingStyleSchema),
        }


class CodeSchema(Schema):
    style = fields.Str(
        dump_default="monokai",
        validate=validate.OneOf(list(pygments.styles.get_all_styles())),
    )
    bg_override = fields.Str(dump_default="")
    inline_lang = fields.Str(dump_default="text")


table_border_default = cast(Dict, BorderBoxSchema().dump(None))
for k, v in table_border_default.items():
    table_border_default[k]["fg"] = "bold,#c0c0c0"


class TableSchema(Schema):
    column_spacing = fields.Int(dump_default=3)
    bg = fields.Str(dump_default="")
    fg = fields.Str(dump_default="")
    header_divider = fields.Nested(
        TextStyleFieldSchema,
        dump_default=TextStyleFieldSchema().dump(
            {
                "text": "─",
                "fg": "bold",
                "bg": "",
            }
        ),
    )
    header = fields.Nested(
        StyleFieldSchema,
        dump_default=StyleFieldSchema().dump(
            {
                "fg": "",
                "bg": "#101010",
            }
        ),
    )
    even_rows = fields.Nested(
        StyleFieldSchema,
        dump_default=StyleFieldSchema().dump(
            {
                "fg": "",
                "bg": "",
            }
        ),
    )
    odd_rows = fields.Nested(
        StyleFieldSchema,
        dump_default=StyleFieldSchema().dump(
            {
                "fg": "",
                "bg": "#0c0c0c",
            }
        ),
    )
    border = fields.Nested(
        BorderBoxSchema,
        dump_default=BorderBoxSchema().dump(
            {
                "tl_corner": {"text": "┌", "fg": line_color, "bg": ""},
                "l_line": {"text": "│", "fg": line_color, "bg": ""},
                "bl_corner": {"text": "└", "fg": line_color, "bg": ""},
                "b_line": {"text": "─", "fg": line_color, "bg": ""},
                "r_line": {"text": "│", "fg": line_color, "bg": ""},
                "t_line": {"text": "─", "fg": line_color, "bg": ""},
                "br_corner": {"text": "┘", "fg": line_color, "bg": ""},
                "tr_corner": {"text": "┐", "fg": line_color, "bg": ""},
            }
        ),
    )


class ScrollbarGutterSchema(Schema):
    """Schema for the slider on the scrollbar"""

    fill = fields.Str(dump_default="▕")
    fg = fields.Str(dump_default="#2c2c2c")
    bg = fields.Str(dump_default="")


class ScrollbarSliderSchema(Schema):
    """Schema for the slider on the scrollbar"""

    top_chars = fields.List(
        fields.Str(), dump_default=["⡀", "⣀", "⣠", "⣤", "⣦", "⣶", "⣾", "⣿"]
    )
    fill = fields.Str(dump_default="⣿")
    bottom_chars = fields.List(
        fields.Str(), dump_default=["⠈", "⠉", "⠋", "⠛", "⠻", "⠿", "⡿", "⣿"]
    )
    fg = fields.Str(dump_default="#4c4c4c")
    bg = fields.Str(dump_default="")


class ScrollbarSchema(Schema):
    """Schema for the scroll bar"""

    gutter = fields.Nested(
        ScrollbarGutterSchema, dump_default=ScrollbarGutterSchema().dump(None)
    )
    slider = fields.Nested(
        ScrollbarSliderSchema, dump_default=ScrollbarSliderSchema().dump(None)
    )


class StyleSchema(Schema):
    """Styles schema for themes and style overrides within presentations"""

    class Meta:
        render_module = YamlRender
        unknown = RAISE

    title = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#f30,bold,italics",
            "bg": "default",
        },
    )
    author = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#f30",
            "bg": "default",
        },
    )
    date = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#777",
            "bg": "default",
        },
    )
    slides = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#ffffff",
            "bg": "#000000",
        },
    )
    slide_number = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#f30",
            "bg": "default",
        },
    )
    margin = fields.Nested(
        SpacingSchema,
        dump_default={
            "top": 0,
            "bottom": 0,
            "left": 2,
            "right": 2,
        },
    )
    padding = fields.Nested(
        SpacingSchema,
        dump_default={
            "top": 1,
            "bottom": 1,
            "left": 10,
            "right": 10,
        },
    )
    headings = fields.Nested(HeadingsSchema, dump_default=HeadingsSchema().dump(None))
    bullets = fields.Nested(BulletsSchema, dump_default=BulletsSchema().dump(None))
    numbering = fields.Nested(
        NumberingSchema, dump_default=NumberingSchema().dump(None)
    )
    code = fields.Nested(CodeSchema, dump_default=CodeSchema().dump(None))
    table = fields.Nested(TableSchema, dump_default=TableSchema().dump(None))
    quote = fields.Nested(BlockQuoteSchema, dump_default=BlockQuoteSchema().dump(None))
    hrule = fields.Nested(HruleSchema, dump_default=HruleSchema().dump(None))
    link = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "#33c,underline",
            "bg": "default",
        },
    )
    emphasis = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "italics",
            "bg": "default",
        },
    )
    strong_emphasis = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "bold",
            "bg": "default",
        },
    )
    strikethrough = fields.Nested(
        StyleFieldSchema,
        dump_default={
            "fg": "strikethrough",
            "bg": "default",
        },
    )
    scrollbar = fields.Nested(
        ScrollbarSchema, dump_default=ScrollbarSchema().dump(None)
    )


class MetaSchema(Schema):
    """The schema for presentation metadata"""

    class Meta:
        render_module = YamlRender
        unknown = INCLUDE

    title = fields.Str(dump_default="", load_default="")
    date = fields.Str(
        dump_default=datetime.datetime.now().strftime("%Y-%m-%d"),
        load_default=datetime.datetime.now().strftime("%Y-%m-%d"),
    )
    author = fields.Str(dump_default="", load_default="")
    theme = fields.Str(dump_default="dark", load_default="dark")
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
