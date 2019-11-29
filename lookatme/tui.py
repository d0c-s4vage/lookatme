"""
This module defines the text user interface (TUI) for lookatme
"""


import copy
import urwid


import lookatme.config
import lookatme.contrib
import lookatme.render.markdown_block as lam_md
from lookatme.utils import *


palette = [
    ('banner', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'black'),
]


def text(style, data, align="left"):
    return urwid.Text((style, data), align=align)


class CurrentSlide(urwid.Frame):
    def __init__(self, pres, palette, idx=0):
        self.slide_body = urwid.Pile(urwid.SimpleListWalker([urwid.Text("test")]))
        self.slide_title = text("banner", f"  {pres.meta.title}  ", "center")

        self.creation = text("banner", f"  {pres.meta.author} - {pres.meta.date}  ")
        self.slide_num = text("banner", " test ", "right")
        self.slide_footer = urwid.Columns([self.creation, self.slide_num])

        self._log = lookatme.config.LOG

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            urwid.Padding(self, left=2, right=2),
            palette,
            screen=screen,
            #unhandled_input=self.handle_input,
        )

        self.pres = pres
        self.curr_slide = self.pres.slides[idx]
        self.slide_cache = {}
        self.update()

        urwid.Frame.__init__(
            self,
            urwid.Padding(urwid.Filler(self.slide_body, valign="top", top=2), left=10, right=10),
            self.slide_title,
            self.slide_footer,
        )

    def update_slide_num(self):
        """Update the slide number
        """
        slide_text = "slide {} / {}".format(
            self.curr_slide.number + 1,
            len(self.pres.slides),
        )
        self.slide_num.set_text(slide_text)

    def update_title(self):
        """Update the title
        """

    def update_body(self):
        """Render the provided slide body
        """
        slide_num = self.curr_slide.number
        if slide_num not in self.slide_cache:
            stack = [self.slide_body]
            self.slide_body.contents = []
            for token in self.curr_slide.tokens:
                self._log.debug(f"{'  '*len(stack)}Rendering token {token}")

                last_stack = stack[-1]
                last_stack_len = len(stack)

                #render_token = getattr(lam_md, f"render_{token['type']}", lambda *args: None)
                render_token = getattr(lam_md, f"render_{token['type']}")
                res = render_token(token, stack[-1], stack, self.loop)
                if len(stack) > last_stack_len:
                    self._propagate_meta(last_stack, stack[-1])
                if res is None:
                    continue
                pile_add(last_stack, res)

            self.slide_cache[slide_num] = list(self.slide_body.contents)
        else:
            self.slide_body.contents = self.slide_cache[slide_num]

    def update(self):
        """
        """
        self.update_slide_num()
        self.update_title()
        self.update_body()

    def _propagate_meta(self, item1, item2):
        """Copy the metadata from item1 to item2
        """
        meta = getattr(item1, "meta", {})
        existing_meta = getattr(item2, "meta", {})
        new_meta = copy.deepcopy(meta)
        new_meta.update(existing_meta)
        setattr(item2, "meta", new_meta)

    def keypress(self, size, key):
        """Handle keypress events
        """
        try:
            res = urwid.Frame.keypress(self, size, key)
            if res is None:
                return
            size, key = res
        except:
            pass

        slide_direction = 0
        if key in ["left", "up", "delete", "h", "k"]:
            slide_direction = -1
        elif key in ["right", "down", " ", "j", "l"]:
            slide_direction = 1
        elif key in ["q", "Q"]:
            lookatme.contrib.shutdown_contribs()
            raise urwid.ExitMainLoop()

        if slide_direction != 0:
            new_slide_num = self.curr_slide.number + slide_direction
            if new_slide_num < 0:
                new_slide_num = 0
            elif new_slide_num >= len(self.pres.slides):
                new_slide_num = len(self.pres.slides) - 1

            if new_slide_num == self.curr_slide.number:
                return

            self.curr_slide = self.pres.slides[new_slide_num]
            self.update()
            self.loop.draw_screen()
            return

    def run(self):
        self.loop.run()



def run_presentation(pres, start_slide=0, width=None, height=None):
    """Run the provided presentation

    :param int start_slide: 0-based slide index
    :param int width: Width of the presentation - defaults to terminal width
    :param int height: Width of the presentation - defaults to terminal height
    """
    slide = CurrentSlide(pres, palette)
    slide.run()
