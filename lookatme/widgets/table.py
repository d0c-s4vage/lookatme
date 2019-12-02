"""
Defines a basic Table widget for urwid
"""


from collections import defaultdict
import urwid


from lookatme.render.markdown_block import render_text
import lookatme.config as config
from lookatme.utils import styled_text


class Table(urwid.Pile):
    """Create a table from a list of headers, alignment values, and rows.
    """

    def __init__(self, rows, headers=None, aligns=None):
        """Create a new table

        :param list columns: The rows to use for the table
        :param list headers: (optional) Headers for the table
        :param list aligns: (optional) Alignment values for each column
        """
        self.table_rows = rows
        self.table_headers = headers
        self.table_aligns = aligns

        if headers is not None:
            self.num_columns = len(headers)
        elif headers is None:
            self.num_columns = len(rows[0])
        else:
            raise ValueError(
                "Invalid table specification: could not determine # of columns"
            )

        def header_modifier(cell):
            return urwid.Text(styled_text(cell, "bold"), align=cell.align)

        if self.table_headers is not None:
            self.rend_headers = self.create_cells(
                [self.table_headers], modifier=header_modifier
            )
        else:
            self.rend_headers = []
        self.rend_rows = self.create_cells(self.table_rows)

        self.column_maxes = self.calc_column_maxes()

        cell_spacing = config.STYLE["table"]["column_spacing"]
        self.total_width = sum(self.column_maxes.values()) + (
            cell_spacing * (self.num_columns - 1)
        )

        # final rows
        final_rows = []

        # put headers in Columns
        if self.table_headers is not None:
            header_columns = []
            for idx, header in enumerate(self.rend_headers[0]):
                header_with_div = urwid.Pile([
                    header,
                    urwid.Divider(config.STYLE["table"]["header_divider"]),
                ])
                header_columns.append((self.column_maxes[idx], header_with_div))
            final_rows.append(urwid.Columns(header_columns, cell_spacing))

        for row_idx, rend_row in enumerate(self.rend_rows):
            row_columns = []
            for idx, rend_cell in enumerate(rend_row):
                row_columns.append((self.column_maxes[idx], rend_cell))

            column_row = urwid.Columns(row_columns, cell_spacing)
            final_rows.append(column_row)
        
        urwid.Pile.__init__(self, final_rows)

    def calc_column_maxes(self):
        column_maxes = defaultdict(int)
        for row in self.rend_headers + self.rend_rows:
            for idx, cell in enumerate(row):
                if idx > self.num_columns:
                    break
                column_maxes[idx] = max(column_maxes[idx], len(cell.text))
        return column_maxes

    def create_cells(self, body_rows, modifier=None):
        """Create the rows for the body, optionally calling a modifier function
        on each created cell Text. The modifier must accept an urwid.Text object
        and must return an urwid.Text object.
        """
        res = []

        for row in body_rows:
            rend_row = []
            for idx, cell in enumerate(row):
                if idx >= self.num_columns:
                    break
                rend_cell = render_text(text=cell)
                rend_cell.align = self.table_aligns[idx] or "left"
                if modifier is not None:
                    rend_cell = modifier(rend_cell)
                rend_row.append(rend_cell)
            res.append(rend_row)

        return res
