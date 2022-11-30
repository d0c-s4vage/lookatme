"""
Defines a basic Table widget for urwid
"""


import re
from collections import defaultdict
from distutils.version import StrictVersion
from typing import Callable, Dict, List, Tuple, Optional

import dateutil.parser
import urwid

import lookatme.config as config
import lookatme.render.markdown_block as markdown_block
import lookatme.utils as utils
from lookatme.render.context import Context


class SortSetting:
    DEFAULT = 0
    ASCENDING = 1
    DESCENDING = 2
    _MAX = 3

    def __init__(self):
        self._header_idx = 0
        self.sort_direction = self.DEFAULT
        self._log = config.get_log().getChild("TableSort")

    def set_indicator(self, idx, text: str):
        if idx != self._header_idx:
            return text

        if self.sort_direction == self.DEFAULT:
            return text
        elif self.sort_direction == self.ASCENDING:
            return "↑" + text[1:]
        else:
            return "↓" + text[1:]

    def get_header_idx(self) -> int:
        return self._header_idx

    def set_header_idx(self, idx):
        if idx != self._header_idx:
            self.sort_direction = self.ASCENDING
        else:
            self.sort_direction = (self.sort_direction + 1) % self._MAX
        self._header_idx = idx
        self._log.debug(
            "Set new header idx, sort direction: {}".format(self.sort_direction)
        )

    def sort_data(self, contents: List[Tuple[int, bytes]]) -> List[int]:
        """Sort the provided data based on the bytes values in the tuples"""
        if self.sort_direction == self.DEFAULT:
            return [x[0] for x in contents]

        casting = self.get_casting([x[1] for x in contents])
        return [
            x[0]
            for x in sorted(
                contents,
                key=lambda x: casting(x[1]),
                reverse=(self.sort_direction == self.DESCENDING),
            )
        ]

    def get_casting(self, data: List[bytes]) -> Callable:
        tests = [
            # floats and ints
            (float, lambda x: re.match(r"^-?[0-9]+(\.[0-9]*)?$", x.decode())),
            # hex numbers!
            (
                lambda x: int(x, 16),
                lambda x: re.match(r"^-?0x[0-9a-fA-F]+$", x.decode()),
            ),
            # version number sorting
            (
                lambda x: StrictVersion(re.sub(r"^v?(.*)$", r"\1", x.decode())),
                lambda x: re.match(r"v?\d+(\.\d+)+", x.decode()) is not None,
            ),
            # fuzzy date parsing
            (dateutil.parser.parse, lambda x: dateutil.parser.parse(x) is not None),
            # default, no change
            (lambda x: x, lambda _: True),
        ]

        for conversion, test_fn in tests:
            all_match = True
            for item in data:
                try:
                    res = test_fn(item)
                except Exception:
                    all_match = False
                    break
                if not res:
                    all_match = False
                    break
            if all_match:
                return conversion

        return lambda x: x


class Table(urwid.Pile):
    signals = ["change"]

    def __init__(self, ctx: Context, header: Dict, body: Optional[Dict]):
        """Create a new table"""
        self.ctx = ctx

        self.header = header
        self.header_rows = []
        self.validate_row_container(self.header)

        self.body = body
        self.body_rows = []
        if self.body is not None:
            self.validate_row_container(self.body)
        self.normalize_body()

        self.num_columns = 0
        self.sort_setting = SortSetting()

        self.style = config.get_style()["table"]
        self.cell_spacing = self.style["column_spacing"]

        self.spec_general = self.ctx.spec_general
        self.spec_text = self.ctx.spec_text

        self.header_spec = utils.spec_from_style(self.style["header"])
        self.header_spec_text = utils.overwrite_spec(self.spec_text, self.header_spec)
        self.header_spec_general = utils.overwrite_spec(
            self.spec_general, self.header_spec
        )

        self.even_spec = utils.spec_from_style(self.style["even_rows"])
        self.even_spec_text = utils.overwrite_spec(self.spec_text, self.even_spec)
        self.even_spec_general = utils.overwrite_spec(self.spec_general, self.even_spec)

        self.odd_spec = utils.spec_from_style(self.style["odd_rows"])
        self.odd_spec_text = utils.overwrite_spec(self.spec_text, self.odd_spec)
        self.odd_spec_general = utils.overwrite_spec(self.spec_general, self.odd_spec)

        self._log = config.get_log().getChild("Table")

        if header is not None:
            self.num_columns = len(header["children"][0]["children"])
        else:
            raise ValueError("Invalid table: could not determine # of columns")

        if self.header is not None:
            if len(self.header["children"]) != 1:
                raise ValueError("Token error: thead should only have one child!")

            self.header_rows = self.create_cells(
                self.header["children"],
                base_spec=ctx.spec_text_with(
                    utils.spec_from_style(self.style["header"])
                ),
                header=True,
            )

        if self.body is not None:
            self.body_rows = self.create_cells(self.body["children"])

        self.column_maxes = self.calc_column_maxes()
        self._log.debug("colum_maxes: {}".format(self.column_maxes))

        self.total_width = sum(self.column_maxes.values()) + (
            self.cell_spacing * (self.num_columns - 1)
        )

        super().__init__([urwid.Text("hello")])

        self.contents = self.gen_contents()
        self._invalidate()

    def normalize_body(self):
        """Normalize the cells in the body - truncate all cells that go beyond
        the number of headers, and add blank cells if we're missing any
        """
        if self.body is None:
            return

        num_cols = len(self.header["children"][0]["children"])
        for row in self.body["children"]:
            while len(row["children"]) < num_cols:
                row["children"].append({"type": "td_open", "children": []})
            # truncate the number of cells
            row["children"] = row["children"][:num_cols]

    def validate_row(self, row: Dict):
        """Validate that the provided row is a tr_open, with th_open or td_open
        children.
        """
        if not isinstance(row, dict):
            raise ValueError("Table rows must be a dict")

        if row["type"] not in ("thead_open", "tr_open"):
            raise ValueError("Rows must be of type thead_open or tr_open")

        for child in row["children"]:
            if child["type"] not in ("th_open", "td_open"):
                raise ValueError(
                    "Row cells must be th_open or td_open, was {!r}".format(
                        child["type"]
                    )
                )

    def validate_row_container(self, container: Dict):
        """Validate that the list of rows is valid. See ``validate_row`` for
        more details.
        """
        if not isinstance(container, dict):
            raise ValueError("Rows must be a contained in a thead or tbody token")

        for row in container["children"]:
            self.validate_row(row)

    def watch_header(self, idx: int, w: urwid.Widget):
        """Watch the provided widget w for changes"""
        signals = getattr(w, "signals", [])
        if "click" in signals and getattr(w, "header_idx", None) is None:
            w.header_idx = idx
            urwid.connect_signal(w, "click", self.on_header_click)

    def on_header_click(self, w: urwid.Widget):
        self._log.debug("Header idx {} was clicked".format(w.header_idx))
        self.sort_setting.set_header_idx(w.header_idx)
        self._log.debug("Regenerating contents")
        self.contents = self.gen_contents()
        return True

    def get_table_rows(self):
        """Get the current rows in this table. This is where sorting should
        happen!
        """
        res = [] + self.header_rows

        sort_data = []
        sort_header_idx = self.sort_setting.get_header_idx()
        for idx, row in enumerate(self.body_rows):
            sort_cell_lines = row[sort_header_idx].render((100,)).text
            sort_cell_data = b"".join(x.strip() for x in sort_cell_lines)
            sort_data.append((idx, sort_cell_data))

        sorted_indices = self.sort_setting.sort_data(sort_data)
        self._log.debug("new sort indices: {!r}".format(sorted_indices))

        body_tokens = []
        for idx in sorted_indices:
            if self.body is None:
                raise Exception("Table body was unexpectedly None")
            body_tokens.append(self.body["children"][idx])

        if sorted_indices == list(range(len(self.body_rows))):
            body_rows = self.body_rows
        else:
            body_rows = self.create_cells(body_tokens)

        return res + body_rows

    def gen_contents(self):
        """Calculate and set the column maxes for this table"""
        self.total_width = sum(self.column_maxes.values()) + (
            self.cell_spacing * (self.num_columns - 1)
        )

        new_contents = []
        for row_idx, row in enumerate(self.get_table_rows()):
            _, row_spec_general = row_specs = self.row_specs(row_idx, row_idx == 0)
            new_columns = self.gen_cells(row, row_specs)
            new_column_w = urwid.Columns(new_columns)
            new_column_w = self.ctx.wrap_widget(new_column_w, row_spec_general)
            new_contents.append((new_column_w, ("weight", 1)))

        return new_contents

    def gen_cells(
        self, row: List[urwid.Pile], row_specs: Tuple[urwid.AttrSpec, urwid.AttrSpec]
    ) -> List[Tuple[int, urwid.Pile]]:
        row_spec_text, row_spec_general = row_specs
        res = []
        for idx, cell_pile in enumerate(row):
            # add the padding between columns if we're not the first column
            if idx > 0:
                padding_text = " " * self.cell_spacing
                padding_w = urwid.Text((row_spec_general, padding_text))
                if cell_pile.is_header and self.body_rows:
                    div_text = self.style["header_divider"]["text"] * len(padding_text)
                    # in case the divider text is more than one char, we'll
                    # truncate it
                    div_text = div_text[: len(padding_text)]
                    div_spec = utils.overwrite_spec(
                        row_spec_text,
                        utils.spec_from_style(self.style["header_divider"]),
                    )
                    padding_w = urwid.Pile(
                        [
                            padding_w,
                            urwid.Text((div_spec, div_text)),
                        ]
                    )

                padding_w = self.ctx.wrap_widget(padding_w, spec=row_spec_general)
                res.append(padding_w)

            if cell_pile.is_header and self.body_rows:
                for w in cell_pile.widget_list:
                    self.watch_header(idx, utils.core_widget(w))

                divider = urwid.Divider(self.style["header_divider"]["text"])
                div_char = self.style["header_divider"]["text"]
                div_spec = utils.overwrite_spec(
                    row_spec_text, utils.spec_from_style(self.style["header_divider"])
                )
                markup = div_char * self.column_maxes[idx]
                markup = self.sort_setting.set_indicator(idx, markup)
                if div_spec is not None:
                    markup = (div_spec, markup)
                divider = urwid.Text(markup)
                divider = self.ctx.wrap_widget(divider, spec=row_spec_text)
                cell_pile = urwid.Pile(cell_pile.widget_list + [divider])

            res.append((self.column_maxes[idx], cell_pile))

        return res

    def calc_column_maxes(self):
        column_maxes = defaultdict(int)
        # list of urwid.Columns
        for row in self.header_rows + self.body_rows:
            # list of urwid.Piles
            for idx, cell in enumerate(row):
                curr_col_width = utils.packed_widget_width(cell)
                column_maxes[idx] = max(column_maxes[idx], curr_col_width)

        return column_maxes

    def _calc_canvas_width(self, canvas):
        canvas_max = 0
        for row in canvas.content():
            row_width = 0
            for spec, _, text in row:
                if spec is None:
                    continue
                row_width += len(text)
            if row_width > canvas_max:
                canvas_max = row_width
        return canvas_max

    def create_cells(
        self, rows, base_spec=None, header=False
    ) -> List[List[urwid.Pile]]:
        """Create the rows for the body, optionally calling a modifier function
        on each created cell Text. The modifier must accept an urwid.Text object
        and must return an urwid.Text object.
        """
        res = []

        if base_spec is not None:
            self.ctx.spec_push(base_spec)

        # should be a list of [tr_open, ...]
        for row_idx, row in enumerate(rows):
            row_spec_text, row_spec_general = self.row_specs(row_idx + 1, header)
            rend_row = []

            # should be a list of [td_open, ...] or [th_open, ...]
            for idx, cell in enumerate(row["children"]):
                if idx >= self.num_columns:
                    break
                cell_container = urwid.Pile([])
                cell_container.is_header = header

                with self.ctx.use_tokens(cell["children"]):
                    with self.ctx.use_container_tmp(cell_container):
                        with self.ctx.use_spec(row_spec_general, text_only=False):
                            with self.ctx.use_spec(row_spec_text, text_only=True):
                                markdown_block.render_all(self.ctx)

                # set alignment for all text widgets
                for widget in cell_container.widget_list:
                    widget = utils.core_widget(widget)
                    if isinstance(widget, urwid.Text):
                        widget.align = cell.get("align", "left") or "left"

                rend_row.append(cell_container)

            # we'll adjust the spacing later!
            res.append(rend_row)

        if base_spec is not None:
            self.ctx.spec_pop()

        return res

    def row_specs(
        self, row_idx: int, is_header: bool
    ) -> Tuple[urwid.AttrSpec, urwid.AttrSpec]:
        """Return the row-specific specs (text and general) for the given row"""
        if is_header:
            row_spec_text = self.header_spec_text
            row_spec_general = self.header_spec_general
        elif row_idx % 2 == 1:
            row_spec_text = self.even_spec_text
            row_spec_general = self.even_spec_general
        else:
            row_spec_text = self.odd_spec_text
            row_spec_general = self.odd_spec_general

        return (row_spec_text, row_spec_general)
