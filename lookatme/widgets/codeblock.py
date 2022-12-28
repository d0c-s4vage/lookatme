"""
This module defines an urwid Widget that renders a codeblock
"""


import itertools
import re
from typing import Dict, List, Mapping, Optional, Set, Tuple


import pygments
from pygments.lexer import Lexer
import pygments.lexers
import pygments.styles
from pygments.style import StyleMeta
import pygments.util
import pygments.token
import urwid


from lookatme.widgets.smart_attr_spec import SmartAttrSpec
from lookatme.widgets.line_fill import LineFill
import lookatme.utils as utils
import lookatme.utils.colors as colors


AVAILABLE_LEXERS = set()


def supported_langs() -> Set[str]:
    global AVAILABLE_LEXERS

    if len(AVAILABLE_LEXERS) == 0:
        AVAILABLE_LEXERS = set(
            itertools.chain(*[x[1] for x in pygments.lexers.get_all_lexers()])
        )

    return AVAILABLE_LEXERS


LEXER_CACHE: Dict[str, Lexer] = {}


def get_lexer(lang, default="text") -> Lexer:
    lexer = LEXER_CACHE.get(lang, None)
    if lexer is None:
        try:
            lexer = pygments.lexers.get_lexer_by_name(lang)
        except pygments.util.ClassNotFound:
            lexer = pygments.lexers.get_lexer_by_name(default)
        LEXER_CACHE[lang] = lexer
    return lexer


def supported_styles() -> Mapping[str, str]:
    return pygments.styles.STYLE_MAP


class SyntaxHlStyle:
    """Stores urwid styles for each token type for a specific pygments syntax
    highlighting style.
    """

    def __init__(
        self,
        name: str,
        styles: Dict[str, SmartAttrSpec],
        pygments_style: StyleMeta,
        default_fg: str,
        bg_override: Optional[str] = None,
    ):
        self.name = name
        self.styles = styles
        self.pygments_style = pygments_style
        self.default_fg = default_fg
        self.bg_override = bg_override

        bg_color = self.bg_override or self.pygments_style.background_color
        self.bg_spec = SmartAttrSpec(fg="", bg=bg_color)
        hl_color = colors.get_highlight_color(bg_color)
        self.highlight_spec = SmartAttrSpec("bold", hl_color)

        if self.bg_override:
            self.bg_spec.background = bg_override

        self.line_number_spec = utils.overwrite_spec(
            SmartAttrSpec(
                fg=self._to_urwid_color(
                    self.pygments_style.line_number_color,
                    self.default_fg,
                ),
                bg=self._to_urwid_color(
                    self.pygments_style.line_number_background_color,
                    self.bg_spec.background,  # type: ignore
                ),
            ),
            self.get_style_spec("Token.Comment", False),
        )
        self.line_number_spec_hl = utils.overwrite_spec(
            self.line_number_spec, self.highlight_spec
        )

    def _to_urwid_color(self, val: str, inherit_val: str) -> str:
        if val in ("inherit", "transparent", None):
            return inherit_val
        return val

    def get_line_number_spec(self, do_hl: bool = False) -> SmartAttrSpec:
        if do_hl:
            return self.line_number_spec_hl
        else:
            return self.line_number_spec

    def get_style_spec(self, token_type: str, highlight: bool) -> SmartAttrSpec:
        """Attempt to find the closest matching style for the provided token
        type.
        """
        token_type = str(token_type)
        parts = token_type.split(".")
        spec = None
        while len(token_type) > 0:
            token_type = ".".join(parts)
            existing_style = self.styles.get(token_type, None)
            if existing_style is not None:
                spec = existing_style
                break
            parts = parts[:-1]

        if spec is None:
            spec = self.styles[token_type]

        if highlight:
            spec = utils.overwrite_spec(spec, self.highlight_spec)
        else:
            spec = utils.overwrite_spec(spec, self.bg_spec)

        if "default" in spec.foreground:
            spec.foreground = utils.overwrite_style(
                {"fg": spec.foreground}, {"fg": self.default_fg}
            )["fg"]

        colors.ensure_contrast(spec)

        return spec


class StyleCache:
    """Caches the highlight styles for loaded pygments syntax highlighting
    styles.
    """

    def __init__(
        self,
        default_fg: Optional[str] = None,
        bg_override: Optional[str] = None,
    ):
        self.default_fg = default_fg or "default"
        self.bg_override = bg_override
        self.cache: Dict[str, SyntaxHlStyle] = {}

    def get_style(self, style_name: str) -> SyntaxHlStyle:
        """Return the highlight style for the specified pygments style name. If
        the style name isn't found, the "text" style will be used instead.
        """
        if style_name not in self.cache:
            self.cache[style_name] = self.load_style(style_name)

        return self.cache[style_name]

    def is_valid_style(self, style_name: str) -> bool:
        """Return whether the style name is a valid pygments style"""
        return style_name in supported_styles()

    def load_style(self, style_name: str) -> SyntaxHlStyle:
        if not self.is_valid_style(style_name):
            style_name = "text"

        pygments_style = pygments.styles.get_style_by_name(style_name)
        style_dict = {}
        for token_type, style_info in pygments_style:
            fg_color = style_info.get("color", None)
            fg = "#" + fg_color if fg_color else "default"

            bg_color = style_info.get("bgcolor", None)
            bg = "#" + bg_color if bg_color else "default"

            if style_info.get("bold", False):
                fg += ",bold"  # type: ignore
            if style_info.get("italics", False):
                fg += ",italics"  # type: ignore
            if style_info.get("underline", False):
                fg += ",underline"  # type: ignore

            style_dict[str(token_type)] = SmartAttrSpec(fg, bg)

        return SyntaxHlStyle(
            style_name,
            style_dict,
            pygments_style,
            default_fg=self.default_fg,
            bg_override=self.bg_override,
        )


STYLE_CACHE = None


def clear_cache():
    global STYLE_CACHE

    STYLE_CACHE = None
    LEXER_CACHE.clear()


def get_style_cache(
    default_fg: Optional[str] = None,
    bg_override: Optional[str] = None,
) -> StyleCache:
    global STYLE_CACHE

    if STYLE_CACHE is None:
        STYLE_CACHE = StyleCache(default_fg, bg_override)

    return STYLE_CACHE


def tokens_to_markup(
    line: List[Tuple[str, str]], style: SyntaxHlStyle, do_hl: bool = False
) -> List[Tuple[SmartAttrSpec, str]]:
    res = []
    for token_type, token_val in line:
        spec = style.get_style_spec(token_type, do_hl)
        res.append((spec, token_val))
    if len(res) == 0:
        res.append("")
    return res


def tokens_to_lines(tokens) -> List[List[Tuple[str, str]]]:
    lines = []
    curr_line = []
    token_stack = list(reversed([x for x in tokens]))
    while len(token_stack) > 0:
        ttype, tstring = token_stack.pop()

        if "\n" in tstring and tstring != "\n":
            for line_part in reversed(re.split(r"(\n)", tstring)):
                if len(line_part) == 0:
                    continue
                token_stack.append((ttype, line_part))
            continue

        if tstring == "\n":
            lines.append(curr_line)
            curr_line = []
            continue

        curr_line.append((ttype, tstring))

    return lines


class CodeBlock(urwid.Pile):
    def __init__(
        self,
        source: str,
        lang: str = "text",
        style_name: str = "monokai",
        line_numbers: bool = False,
        start_line_number: int = 1,
        hl_lines: Optional[List[range]] = None,
        default_fg: Optional[str] = None,
        bg_override: Optional[str] = None,
    ):
        self.source = source
        self.lang = lang
        self.line_numbers = line_numbers
        self.start_line_number = start_line_number
        self.hl_lines = hl_lines or []

        self.style = get_style_cache(
            default_fg=default_fg,
            bg_override=bg_override,
        ).get_style(style_name)

        contents = self._create_contents()

        super().__init__(contents)

    def _create_contents(self) -> List[urwid.Columns]:
        """Create the contents that will be used in the Pile"""
        tokens = get_lexer(self.lang).get_tokens(self.source)
        res = []

        lines = tokens_to_lines(tokens)

        max_line_num_width = len(str(self.start_line_number + len(lines)))
        line_num_format_str = " {:" + str(max_line_num_width) + "} "
        line_num_col_width = len(line_num_format_str.format(0))

        for idx, line in enumerate(lines):
            line_num = idx + self.start_line_number
            do_hl = self._should_hl_line(line_num)
            columns = []
            box_columns = []

            if self.line_numbers:
                line_num_text = line_num_format_str.format(line_num)
                line_num_spec = self.style.get_line_number_spec(do_hl)
                columns.append(
                    (line_num_col_width, urwid.Text((line_num_spec, line_num_text)))
                )
                columns.append(
                    (
                        1,
                        LineFill(
                            beg_chars="",
                            fill_char="│",
                            end_chars="",
                            fill_spec=line_num_spec,
                            orientation=LineFill.VERTICAL,
                        ),
                    )
                )
                columns.append(
                    (
                        1,
                        LineFill(
                            beg_chars="",
                            fill_char=" ",
                            end_chars="",
                            fill_spec=line_num_spec,
                            orientation=LineFill.VERTICAL,
                        ),
                    )
                )
                box_columns.append(1)
                box_columns.append(2)

            line_text = urwid.Text(tokens_to_markup(line, self.style, do_hl))
            columns.append(line_text)

            row = urwid.Columns(columns, box_columns=box_columns)

            wrap_spec = self.style.highlight_spec if do_hl else self.style.bg_spec
            row = urwid.AttrMap(row, {None: wrap_spec})

            res.append(row)

        return res

    def _make_line_column(
        self, format_str: str, line_num: int, do_hl: bool
    ) -> urwid.Text:
        text = format_str.format(line_num)
        spec = self.style.get_line_number_spec(do_hl)
        return urwid.Text((spec, text))

    def _should_hl_line(self, line_num: int) -> bool:
        for hl_range in self.hl_lines:
            if line_num in hl_range:
                return True
        return False
