"""
Defines a basic Table widget for urwid
"""


from collections import defaultdict
import urwid


from lookatme.render.markdown_block import render_tokens_full
import lookatme.config as config
from lookatme.utils import styled_text, spec_from_style, get_meta
from lookatme.widgets.clickable_text import ClickableText
import lookatme.render.markdown_inline as markdown_inline
from lookatme.render.context import Context


class Table(urwid.Pile):
    """Create a table from a list of headers, alignment values, and rows.
    """

    signals = ["change"]

    def __init__(self, ctx, header=None, body=None):
        """Create a new table

        :param list columns: The rows to use for the table
        :param list headers: (optional) Headers for the table
        :param list aligns: (optional) Alignment values for each column
        """
        self.ctx = ctx
        self.header = header
        self.body = body

        self._log = config.LOG.getChild("Table")

        if header is not None:
            self.num_columns = len(header["children"])
        elif body is not None:
            self.num_columns = max(len(row["children"]) for row in body["children"])
        else:
            raise ValueError(
                "Invalid table specification: could not determine # of columns"
            )

        if self.header is not None:
            self.rend_headers = self.create_cells(
                [{"children": self.header["children"]}],
                base_spec=spec_from_style("bold"),
            )
        else:
            self.rend_headers = []

        if self.body is not None:
            self.rend_rows = self.create_cells(self.body["children"])
        else:
            self.rend_rows = []

        self.column_maxes = self.calc_column_maxes()

        cell_spacing = config.STYLE["table"]["column_spacing"]
        self.total_width = sum(self.column_maxes.values()) + (
            cell_spacing * (self.num_columns - 1)
        )

        # final rows
        final_rows = []

        # put headers in Columns
        if self.header is not None:
            header_columns = []
            for idx, header in enumerate(self.rend_headers[0]):
                header = header[0]
                self.watch(header)
                get_meta(header)["col_idx"] = idx
                header_with_div = urwid.Pile([
                    header,
                    urwid.Divider(config.STYLE["table"]["header_divider"]),
                ])
                header_columns.append((self.column_maxes[idx], header_with_div))
            final_rows.append(urwid.Columns(header_columns, cell_spacing))

        for row_idx, rend_row in enumerate(self.rend_rows):
            row_columns = []
            for cell_idx, rend_cell in enumerate(rend_row):
                map(lambda w: self.watch(w), rend_cell)
                rend_pile = urwid.Pile(rend_cell)
                row_columns.append((self.column_maxes[cell_idx], rend_pile))

            column_row = urwid.Columns(row_columns, cell_spacing)
            final_rows.append(column_row)
        
        urwid.Pile.__init__(self, final_rows)

    def on_cell_change(self, *args, **kwargs):
        self._invalidate()
        self._emit("change")

    def on_header_click(self, header_widget):
        self._log.debug("Header clicked: {!r}".format(header_widget.text))
        self._emit("click")

    def render(self, *args, **kwargs):
        """Do whatever needs to be done to render the table
        """
        self.set_column_maxes()
        return urwid.Pile.render(self, *args, **kwargs)
    
    def watch(self, w):
        """Watch the provided widget w for changes
        """
        signals = getattr(w, "signals", [])
        if "change" in signals:
            urwid.connect_signal(w, "change", self.on_cell_change)
        if "click" in signals:
            urwid.connect_signal(w, "click", self.on_header_click)
    
    def _invalidate(self):
        self.set_column_maxes()
        urwid.Pile._invalidate(self)

    def set_column_maxes(self):
        """Calculate and set the column maxes for this table
        """
        self.column_maxes = self.calc_column_maxes()
        cell_spacing = config.STYLE["table"]["column_spacing"]
        self.total_width = sum(self.column_maxes.values()) + (
            cell_spacing * (self.num_columns - 1)
        )

        for columns, info in self.contents:
            # row should be a Columns instance
            new_columns = []
            for idx, column_items in enumerate(columns.contents):
                column_widget, column_info = column_items
                new_columns.append((
                    column_widget,
                    (column_info[0], self.column_maxes[idx], column_info[2]),
                ))
            columns.contents = new_columns

    def calc_column_maxes(self):
        column_maxes = defaultdict(int)
        for row in self.rend_headers + self.rend_rows:
            for idx, cell in enumerate(row):
                for widget in cell:
                    if not isinstance(widget, urwid.Text):
                        widg_len = 15
                    else:
                        widg_len = len(widget.text)
                    if idx > self.num_columns:
                        break
                    column_maxes[idx] = max(column_maxes[idx], widg_len)
        return column_maxes

    def create_cells(self, body_rows, base_spec=None):
        """Create the rows for the body, optionally calling a modifier function
        on each created cell Text. The modifier must accept an urwid.Text object
        and must return an urwid.Text object.
        """
        res = []

        if base_spec is not None:
            self.ctx.spec_push(base_spec)

        for row in body_rows:
            rend_row = []
            for idx, cell in enumerate(row["children"]):
                if idx >= self.num_columns:
                    break
                markdown_inline.render_all(cell["children"], self.ctx)
                cell_widgets = self.ctx.inline_widgets_consumed
                new_widgets = []
                for widget in cell_widgets:
                    if isinstance(widget, urwid.Text):
                        widget.align = cell.get("align", "left") or "left"
                    new_widgets.append(widget)
                rend_row.append(new_widgets)
            res.append(rend_row)

        if base_spec is not None:
            self.ctx.spec_pop()

        return res
