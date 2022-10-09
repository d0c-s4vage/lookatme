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


class TableRow(urwid.Widget):
    def __init__(self, cell_tokens: List[Dict]):
        self.cell_tokens = cell_tokens
        self.cell_piles = [self.create_cell(x) for x in cell_tokens]
        self.cell_widths = [self.get_max_width(x) for x in self.cell_piles]

    def get_max_width(self, cell_pile: urwid.Pile) -> int:
        max_width = 0
        __import__("pdb").set_trace()
        for widget in cell_pile.widget_list:
            cols,rows = widget.pack()
            max_width = max(max_width, cols)
        return 15

    def create_cell(self, cell_token: Dict) -> urwid.Pile:
        return urwid.Pile([urwid.Text("cell")])

    # -------------------------------------------------------------------------
    # URWID REQUIRED FUNCTIONS ------------------------------------------------
    # -------------------------------------------------------------------------

    def rows(self, size: Tuple[int, int], focus: bool=False) -> int:
        return 1

    def render(self, size: Tuple[int, int], focus: bool=False) -> urwid.Canvas:
        pass


# http://urwid.org/manual/widgets.html#widgets-from-scratch
# this will be a flow widget
# http://urwid.org/reference/widget.html#urwid.Widget.sizing
class TableNew(urwid.Widget):
    def __init__(self, ctx: Context, header: Dict, body: Dict):
        """Create a new table

        :param list columns: The rows to use for the table
        :param list headers: (optional) Headers for the table
        :param list aligns: (optional) Alignment values for each column
        """
        self.header = header
        self.validate_row_container(self.header)
        self.header_rows = [self.create_row(x) for x in self.header["children"]]

        self.body = body
        self.validate_row_container(self.body)
        self.body_rows = [self.create_row(x) for x in self.body["children"]]

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

    def create_row(self, row: Dict) -> TableRow:
        """Create a new TableRow instance from the provided markdown tokens
        """
        if row["type"] != "tr_open":
            raise ValueError("tr_open expected")

        # row will be a tr_open token
        return TableRow(row["children"])

    # -------------------------------------------------------------------------
    # URWID REQUIRED FUNCTIONS ------------------------------------------------
    # -------------------------------------------------------------------------

    def rows(self, size: Tuple[int, int], focus: bool = False) -> int:
        return 1

    def render(self, size: Tuple[int, int], focus: bool) -> urwid.Canvas:
        """Render the contents!
        """


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

        self.style = config.get_style()["table"]
        cell_spacing = self.style["column_spacing"]

        self.spec_general = self.ctx.spec_general
        self.spec_text = self.ctx.spec_text

        self.header_spec = utils.spec_from_style(self.style["header"])
        self.header_spec_text = utils.overwrite_spec(self.spec_text, self.header_spec)
        self.header_spec_general = utils.overwrite_spec(self.spec_general, self.header_spec)

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
                raise ValueError(
                    "Token error: thead should only have one child!")

            self.header_rows = self.create_cells(
                self.header["children"],
                base_spec=ctx.spec_text_with(utils.spec_from_style("bold")),
                header=True
            )

        if self.body is not None:
            self.body_rows = self.create_cells(self.body["children"])

        self.column_maxes = self.calc_column_maxes()
        self._log.debug("colum_maxes: {}".format(self.column_maxes))

        self.total_width = (
            sum(self.column_maxes.values())
            + (cell_spacing * (self.num_columns - 1))
        )

        super().__init__([urwid.Text("hello")])

        self.contents = self.gen_contents()
        self._invalidate()

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
            sort_cell_lines = row[sort_header_idx].render((100,)).text
            sort_cell_data = b"".join(x.strip() for x in sort_cell_lines)
            sort_data.append((idx, sort_cell_data))

        sorted_indices = self.sort_setting.sort_data(sort_data)
        self._log.debug("new sort indices: {!r}".format(sorted_indices))

        body_tokens = []
        for idx in sorted_indices:
            body_tokens.append(self.body["children"][idx])

        if sorted_indices == list(range(len(self.body_rows))):
            body_rows = self.body_rows
        else:
            body_rows = self.create_cells(body_tokens)

        return res + body_rows

    def gen_contents(self):
        """Calculate and set the column maxes for this table
        """
        table_style = config.get_style()["table"]
        cell_spacing = table_style["column_spacing"]

        self.total_width = sum(self.column_maxes.values()) + (
            cell_spacing * (self.num_columns - 1)
        )

        new_contents = []
        for row_idx, row in enumerate(self.get_table_rows()):
            row_spec_text, row_spec_general = self.row_specs(row_idx, row_idx==0)

            # row should be a Columns instance
            new_columns = []
            for idx, cell_pile in enumerate(row):
                # add the pdading between columns if we're not the first column
                if idx > 0:
                    padding_text = " " * cell_spacing
                    if cell_pile.is_header:
                        padding_text += "\n" + (self.style["header_divider"]["text"] * cell_spacing) 
                    padding_pile = urwid.Pile([urwid.Text(padding_text)])
                    padding_pile = self.ctx.wrap_widget(padding_pile, spec=row_spec_general)
                    new_columns.append(padding_pile)

                if cell_pile.is_header:
                    for w in cell_pile.widget_list:
                        self.watch_header(idx, utils.core_widget(w))

                    divider = urwid.Divider(self.style["header_divider"]["text"])
                    divider = self.ctx.wrap_widget(divider, spec=row_spec_text)
                    cell_pile = urwid.Pile(
                        cell_pile.widget_list + [divider]
                    )

                #cell_pile = self.ctx.wrap_widget(cell_pile, spec=row_spec_general)
                #padding = urwid.Padding(cell_pile, width=self.column_maxes[idx])
                #padding = self.ctx.wrap_widget(padding, row_spec_general)
                new_columns.append((self.column_maxes[idx], cell_pile))

            new_column_w = urwid.Columns(new_columns)
            new_column_w = self.ctx.wrap_widget(new_column_w, row_spec_general)
            new_contents.append((new_column_w, ('weight', 1)))

        return new_contents

    def calc_column_maxes(self):
        column_maxes = defaultdict(int)
        # list of urwid.Columns
        for row in self.header_rows + self.body_rows:
            # list of urwid.Piles
            for idx, cell in enumerate(row):
                rend = cell.render((200,))
                curr_col_width = max(len(rend_row.strip()) for rend_row in rend.text)
                column_maxes[idx] = max(column_maxes[idx], curr_col_width)

        # reserve one more character for an up/down arrow to indicate the
        # sort direction
        for key in column_maxes.keys():
            column_maxes[key] += 1

        return column_maxes

    def create_cells(self, rows, base_spec=None, header=False) -> List[List[urwid.Pile]]:
        """Create the rows for the body, optionally calling a modifier function
        on each created cell Text. The modifier must accept an urwid.Text object
        and must return an urwid.Text object.
        """
        res = []

        if base_spec is not None:
            self.ctx.spec_push(base_spec)

        # should be a list of [tr_open, ...]
        for row_idx, row in enumerate(rows):
            row_spec_text, row_spec_general = self.row_specs(row_idx+1, header)
            rend_row = []

            # should be a list of [td_open, ...] or [th_open, ...]
            for idx, cell in enumerate(row["children"]):
                if idx >= self.num_columns:
                   break
                cell_container = urwid.Pile([])
                cell_container.is_header = header

                with self.ctx.use_container_tmp(cell_container):
                    with self.ctx.use_spec(row_spec_general, text_only=False):
                        with self.ctx.use_spec(row_spec_text, text_only=True):
                            with self.ctx.use_tokens(cell["children"]):
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
    
    def row_specs(self, row_idx: int, is_header: bool) -> Tuple[urwid.AttrSpec, urwid.AttrSpec]:
        """Return the row-specific specs (text and general) for the given row
        """
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
