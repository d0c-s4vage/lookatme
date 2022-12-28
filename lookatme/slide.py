"""
Slide info holder
"""


from typing import Optional, Tuple


import urwid


from lookatme.render.context import Context
import lookatme.render.markdown_block as markdown_block
import lookatme.utils as utils


class Slide(object):
    """This class defines a single slide. It operates on mistune's lexed
    tokens from the input markdown
    """

    def __init__(self, tokens, number=0):
        """Create a new Slide instance with the provided tokens

        :param list tokens: A list of mistune tokens
        :param int number: The slide number
        """
        self.tokens = tokens
        self.number = number

    def get_title(self, ctx: Context) -> Tuple[str, Optional[urwid.Canvas]]:
        default_result = ("Slide {}".format(self.number), None)

        if not self.tokens:
            return default_result

        if len(self.tokens) < 3:
            return default_result

        first, second, third = self.tokens[:3]
        if first["type"] != "heading_open":
            return default_result
        if second["type"] != "inline":
            return default_result
        if third["type"] != "heading_close":
            return default_result

        tmp = urwid.Pile([])
        heading_tokens = [first, second, third]
        with ctx.use_tokens(heading_tokens):
            with ctx.use_container(tmp, is_new_block=True):
                markdown_block.render_all(ctx)

        min_width = utils.packed_widget_width(tmp)
        canvas = tmp.render((min_width,), False)

        return canvas.text[0].decode(), canvas
