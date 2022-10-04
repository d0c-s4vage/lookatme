"""
Defines a basic Table widget for urwid
"""


from collections import defaultdict
from typing import List, Optional

import urwid

from lookatme.render.context import Context
import lookatme.config as config
import lookatme.utils as utils
import lookatme.render.markdown_inline as markdown_inline
import lookatme.render.markdown_block as markdown_block
from lookatme.render.context import Context


class Table(urwid.Pile):
    """Create a table from a list of headers, alignment values, and rows.
    """

    signals = ["change"]

    def __init__(self, ctx: Context, header=None, body=None):
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

        self.header_rows = []
        if self.header is not None:
            if len(self.header["children"]) != 1:
                raise ValueError("Token error: thead should only have one child!")

            self.header_rows = self.create_cells(
                self.header["children"],
                base_spec=ctx.spec_text_with(utils.spec_from_style("bold")),
                header=True
            )

        self.body_rows = []
        if self.body is not None:
            self.body_rows = self.create_cells(self.body["children"])

#        max_column_widths: Dict[int, int] = self.get_max_column_widths(
#            self.header_rows + self.body_rows,
#        )
        
        super(self.__class__, self).__init__(self.header_rows + self.body_rows)

    # def create_final_rows(self, headers, body_rows):
#        self.column_maxes = self.calc_column_maxes()
#
#        cell_spacing = config.STYLE["table"]["column_spacing"]
#        self.total_width = sum(self.column_maxes.values()) + (
#            cell_spacing * (self.num_columns - 1)
#        )
#
#        # final rows
#        final_rows = []
#
#        # put headers in Columns
#        if self.header is not None:
#            header_columns = []
#            for idx, header in enumerate(self.rend_headers[0]):
#                self.watch(header)
#                get_meta(header)["col_idx"] = idx
#                divider = urwid.Divider(config.STYLE["table"]["header_divider"])
#                pile_or_listbox_add(header, divider)
#                header_columns.append((self.column_maxes[idx], header))
#            final_rows.append(urwid.Columns(header_columns, cell_spacing))
#
#        for row_idx, rend_row in enumerate(self.rend_rows):
#            row_columns = []
#            for cell_idx, rend_cell in enumerate(rend_row):
#                map(lambda w: self.watch(w), rend_cell)
#                rend_pile = urwid.Pile(rend_cell)
#                row_columns.append((self.column_maxes[cell_idx], rend_pile))
#
#            column_row = urwid.Columns(row_columns, cell_spacing)
#            final_rows.append(column_row)
        
#         final_rows = [urwid.Columns(self.rend_headers[0], 10)]
#         for row in self.rend_rows:
#             final_rows.append(urwid.Columns(row, 10))
# 
#         urwid.Pile.__init__(self, final_rows)

#     def on_cell_change(self, *args, **kwargs):
#         self._invalidate()
#         self._emit("change")
# 
#     def on_header_click(self, header_widget):
#         self._log.debug("Header clicked: {!r}".format(header_widget.text))
#         self._emit("click")
# 
#     def render(self, size, focus=False):
#         """Do whatever needs to be done to render the table
#         """
#         self.set_column_maxes()
#         res = super(self.__class__, self).render(size, focus)
#         self._log.debug("self.get_item_rows: {!r}".format(self.get_item_rows(size, focus)))
#         self._log.debug("res: {!r}.rows(): {!r}".format(res, res.rows()))
#         self._log.debug("self.rows(): {!r}".format(self.rows(size)))
#         return res
#     
#     def watch(self, w):
#         """Watch the provided widget w for changes
#         """
#         signals = getattr(w, "signals", [])
#         if "change" in signals:
#             urwid.connect_signal(w, "change", self.on_cell_change)
#         if "click" in signals:
#             urwid.connect_signal(w, "click", self.on_header_click)
#     
#     def _invalidate(self):
#         self.set_column_maxes()
#         urwid.Pile._invalidate(self)
# 
#     def set_column_maxes(self):
#         """Calculate and set the column maxes for this table
#         """
#         self.column_maxes = self.calc_column_maxes()
#         cell_spacing = config.STYLE["table"]["column_spacing"]
#         self.total_width = sum(self.column_maxes.values()) + (
#             cell_spacing * (self.num_columns - 1)
#         )
# 
#         for columns, info in self.contents:
#             # row should be a Columns instance
#             new_columns = []
#             for idx, column_items in enumerate(columns.contents):
#                 column_widget, column_info = column_items
#                 new_columns.append((
#                     column_widget,
#                     (column_info[0], self.column_maxes[idx], column_info[2]),
#                 ))
#             columns.contents = new_columns
# 
#     def calc_column_maxes(self):
#         column_maxes = defaultdict(int)
#         for row in self.rend_headers + self.rend_rows:
#             for idx, cell in enumerate(row):
#                 for widget in cell:
#                     widget = core_widget(widget)
#                     if getattr(widget, "text", None) is None:
#                         widg_len = 15
#                     else:
#                         widg_len = len(widget.text)
#                     if idx > self.num_columns:
#                         break
#                     column_maxes[idx] = max(column_maxes[idx], widg_len)
#         return column_maxes

    def create_cells(self, body_rows, base_spec=None, header=False):
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
                #if idx >= self.num_columns:
                #    break
                cell_container = urwid.Pile([])
                with self.ctx.use_container_tmp(cell_container):
                    with self.ctx.use_tokens(cell["children"]):
                        markdown_block.render_all(self.ctx)
                        if header:
                            divider = urwid.Divider(config.STYLE["table"]["header_divider"])
                            self.ctx.inline_flush()
                            self.ctx.widget_add(divider)

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
