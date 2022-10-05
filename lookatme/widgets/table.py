"""
Defines a basic Table widget for urwid
"""


from collections import defaultdict
import dateutil.parser
from distutils.version import StrictVersion
import re
from typing import Callable, List, Dict, Tuple

import urwid

import lookatme.config as config
import lookatme.render.markdown_block as markdown_block
import lookatme.render.markdown_inline as markdown_inline
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

    def get_header_idx(self) -> int:
        return self._header_idx

    def set_header_idx(self, idx):
        if idx != self._header_idx:
            self.sort_direction = self.ASCENDING
        else:
            self.sort_direction = (self.sort_direction + 1) % self._MAX
        self._header_idx = idx
        self._log.debug("Set new header idx, sort direction: {}".format(
            self.sort_direction
        ))

    def sort_data(self, contents: List[Tuple[int, bytes]]) -> List[int]:
        """Sort the provided data based on the bytes values in the tuples
        """
        if self.sort_direction == self.DEFAULT:
            return [x[0] for x in contents]

        casting = self.get_casting([x[1] for x in contents])
        return [x[0] for x in sorted(
            contents,
            key=lambda x: casting(x[1]),
            reverse=(self.sort_direction == self.DESCENDING)
        )]

    def get_casting(self, data: List[bytes]) -> Callable:
        tests = [
            # floats and ints
            (float, lambda x: re.match(r"^-?[0-9]+(\.[0-9]*)?$", x.decode())),

            # hex numbers!
            (lambda x: int(x, 16), lambda x: re.match(r"^-?0x[0-9a-fA-F]+$", x.decode())),

            # version number sorting
            (
                lambda x: StrictVersion(re.sub(r"^v?(.*)$", r'\1', x.decode())),
                lambda x: re.match(r"v?\d+(\.\d+)+", x.decode()) is not None
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
    """Create a table from a list of headers, alignment values, and rows.
    """

    signals = ["change"]

    def __init__(self, ctx: Context, header: Dict, body: Dict):
        """Create a new table

        :param list columns: The rows to use for the table
        :param list headers: (optional) Headers for the table
        :param list aligns: (optional) Alignment values for each column
        """
        self.ctx = ctx

        self.header = header
        self.header_rows = []
        self.validate_row_container(self.header)

        self.body = body
        self.body_rows = []
        self.validate_row_container(self.body)

        self.num_columns = 0
        self.sort_setting = SortSetting()
        self.spec_general = self.ctx.spec_general
        self.spec_text = self.ctx.spec_text

        self._log = config.get_log().getChild("Table")

        if header is not None:
            self.num_columns = len(header["children"][0]["children"])
        else:
            raise ValueError("Invalid table: could not determine # of columns")

        if self.header is not None:
            if len(self.header["children"]) != 1:
                raise ValueError(
                    "Token error: thead should only have one child!")

            self.header_rows = self.create_cells(
                self.header["children"],
                base_spec=ctx.spec_text_with(utils.spec_from_style("bold")),
                header=True
            )

        if self.body is not None:
            self.body_rows = self.create_cells(self.body["children"])

        cell_spacing = config.get_style()["table"]["column_spacing"]
        self.column_maxes = self.calc_column_maxes()
        self._log.debug("colum_maxes: {}".format(self.column_maxes))

        self.total_width = (
            sum(self.column_maxes.values())
            + (cell_spacing * (self.num_columns - 1))
        )

        super().__init__([urwid.Text("hello")])

        self.contents = self.gen_contents()
#
    def watch_header(self, idx: int, w: urwid.Widget):
        """Watch the provided widget w for changes
        """
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
            sort_cell_lines = row.widget_list[sort_header_idx].render((100,)).text
            sort_cell_data = b"".join(x.strip() for x in sort_cell_lines)
            sort_data.append((idx, sort_cell_data))

        sorted_indices = self.sort_setting.sort_data(sort_data)
        self._log.debug("new sort indices: {!r}".format(sorted_indices))

        for idx in sorted_indices:
            res.append(self.body_rows[idx])

        return res

    def gen_contents(self):
        """Calculate and set the column maxes for this table
        """
        cell_spacing = config.get_style()["table"]["column_spacing"]
        self.total_width = sum(self.column_maxes.values()) + (
            cell_spacing * (self.num_columns - 1)
        )

        new_contents = []
        for row in self.get_table_rows():
            # row should be a Columns instance
            new_columns = []
            for idx, column_items in enumerate(row.contents):
                column_widget, _ = column_items
                if column_widget.is_header:
                    for w in column_widget.widget_list:
                        self.watch_header(idx, utils.core_widget(w))

                    divider = urwid.Divider(
                        config.get_style()["table"]["header_divider"]
                    )
                    divider = self.ctx.wrap_widget(divider, spec=self.spec_text)
                    column_widget = urwid.Pile(
                        column_widget.widget_list + [divider]
                    )
                new_columns.append((self.column_maxes[idx], column_widget))

            cell_spacing = config.get_style()["table"]["column_spacing"]
            new_column_w = urwid.Columns(new_columns, cell_spacing)
            new_contents.append((new_column_w, ('weight', 1)))

        return new_contents

    def calc_column_maxes(self):
        column_maxes = defaultdict(int)
        for row in self.header_rows + self.body_rows:
            for idx, cell in enumerate(row.widget_list):
                rend = cell.render((200,))
                curr_col_width = max(len(rend_row.strip()) for rend_row in rend.text)
                column_maxes[idx] = max(column_maxes[idx], curr_col_width)
        return column_maxes

    def create_cells(self, rows, base_spec=None, header=False):
        """Create the rows for the body, optionally calling a modifier function
        on each created cell Text. The modifier must accept an urwid.Text object
        and must return an urwid.Text object.
        """
        res = []

        if base_spec is not None:
            self.ctx.spec_push(base_spec)

        # should be a list of [tr_open, ...]
        for row in rows:
            rend_row = []
            # should be a list of [td_open, ...] or [th_open, ...]
            for idx, cell in enumerate(row["children"]):
                if idx >= self.num_columns:
                   break
                cell_container = urwid.Pile([])
                cell_container.is_header = header

                with self.ctx.use_container_tmp(cell_container):
                    with self.ctx.use_tokens(cell["children"]):
                        markdown_block.render_all(self.ctx)

                # set alignment for all text widgets
                for widget in cell_container.widget_list:
                    widget = utils.core_widget(widget)
                    if isinstance(widget, urwid.Text):
                        widget.align = cell.get("align", "left") or "left"

                rend_row.append(cell_container)

            # we'll adjust the spacing later!
            column = urwid.Columns(rend_row, 1)
            res.append(column)

        if base_spec is not None:
            self.ctx.spec_pop()

        return res

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
                raise ValueError("Row cells must be th_open or td_open")

    def validate_row_container(self, container: Dict):
        """Validate that the list of rows is valid. See ``validate_row`` for
        more details.
        """
        if not isinstance(container, dict):
            raise ValueError("Rows must be a contained in a thead or tbody token")

        for row in container["children"]:
            self.validate_row(row)
