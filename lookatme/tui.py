"""
This module defines the text user interface (TUI) for lookatme
"""


from collections import defaultdict
import copy
import threading
import time
from queue import Queue
import urwid


import lookatme.config
import lookatme.contrib
import lookatme.render.markdown_block as lam_md
from lookatme.utils import pile_add


palette = [
    ('banner', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'black'),
]


def text(style, data, align="left"):
    return urwid.Text((style, data), align=align)


class SlideRenderer(threading.Thread):
    daemon = True

    def __init__(self, loop):
        threading.Thread.__init__(self)
        self.events = defaultdict(threading.Event)
        self.keep_running = threading.Event()
        self.queue = Queue()
        self.loop = loop
        self.cache = {}
        self._log = lookatme.config.LOG.getChild("RENDER")

    def flush_cache(self):
        """Clea everything out of the queue and the cache.
        """
        # clear all pending items
        with self.queue.mutex:
            self.queue.queue.clear()
        self.cache.clear()

    def queue_render(self, slide):
        """Queue up a slide to be rendered.
        """
        self.events[slide.number].clear()
        self.queue.put(slide)

    def render_slide(self, slide, force=False):
        """Render a slide, blocking until the slide completes. If ``force`` is
        True, rerender the slide even if it is in the cache.
        """
        if not force and slide.number in self.cache:
            return self.cache[slide.number]

        self.events[slide.number].clear()
        self.queue.put(slide)
        self.events[slide.number].wait()

        res = self.cache[slide.number]
        if isinstance(res, Exception):
            raise res
        return res

    def get_slide(self, slide_number):
        """Fetch the slide from the cache
        """
        self.locks[slide_number].wait()
        return self.cache[slide.number]

    def _propagate_meta(self, item1, item2):
        """Copy the metadata from item1 to item2
        """
        meta = getattr(item1, "meta", {})
        existing_meta = getattr(item2, "meta", {})
        new_meta = copy.deepcopy(meta)
        new_meta.update(existing_meta)
        setattr(item2, "meta", new_meta)

    def stop(self):
        self.keep_running.clear()
    
    def run(self):
        """Run the main render thread
        """
        self.keep_running.set()
        while self.keep_running.is_set():
            to_render = self.queue.get()
            slide_num = to_render.number

            try:
                res = self._do_render(to_render, slide_num)
                self.cache[slide_num] = res
            except Exception as e:
                self.cache[slide_num] = e
            finally:
                self.events[slide_num].set()

    def _do_render(self, to_render, slide_num):
        """Perform the actual rendering of a slide
        """
        self._log.debug(f"Rendering slide {slide_num}")
        start = time.time()

        tmp_pile = urwid.Pile([])
        stack = [tmp_pile]
        for token in to_render.tokens:
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

        total = time.time() - start
        self._log.debug(f"Rendered slide {slide_num} in {total}")

        return tmp_pile.contents


class MarkdownTui(urwid.Frame):
    def __init__(self, pres, palette, start_idx=0):
        """
        """
        self.slide_body = urwid.Pile(urwid.SimpleListWalker([urwid.Text("test")]))
        self.slide_title = text("banner", "", "center")

        self.creation = text("banner", "")
        self.slide_num = text("banner", " test ", "right")
        self.slide_footer = urwid.Columns([self.creation, self.slide_num])

        self._log = lookatme.config.LOG

        screen = urwid.raw_display.Screen()
        screen.set_terminal_properties(colors=256)
        self.loop = urwid.MainLoop(
            urwid.Padding(self, left=2, right=2),
            palette,
            screen=screen,
        )

        # used to track slides that are being rendered
        self.slide_renderer = SlideRenderer(self.loop)
        self.slide_renderer.start()

        self.pres = pres
        self.prep_pres(self.pres, start_idx)

        urwid.Frame.__init__(
            self,
            urwid.Padding(urwid.Filler(self.slide_body, valign="top", top=2), left=10, right=10),
            self.slide_title,
            self.slide_footer,
        )

    def prep_pres(self, pres, start_idx=0):
        """Prepare the presentation for displaying/use
        """
        self.curr_slide = self.pres.slides[start_idx]
        self.update()

        # now queue up the rest of the slides while we're at it so they'll be
        # ready when we need them
        for slide in filter(lambda x: x.number != start_idx, self.pres.slides):
            self.slide_renderer.queue_render(slide)

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
        title = self.pres.meta.get("title", "")
        self.slide_title.set_text(f" {title} ")

    def update_creation(self):
        """Update the author and date
        """
        author = self.pres.meta.get('author', '')
        date = self.pres.meta.get('date', '')
        self.creation.set_text(f"  {author} - {date}  ")

    def update_body(self):
        """Render the provided slide body
        """
        rendered = self.slide_renderer.render_slide(self.curr_slide)
        self.slide_body.contents = rendered

    def update(self):
        """
        """
        self.update_slide_num()
        self.update_title()
        self.update_creation()
        self.update_body()

    def reload(self):
        """Reload the input, keeping the current slide in focus
        """
        curr_slide_idx = self.curr_slide.number
        self.slide_renderer.flush_cache()
        self.pres.reload()
        self.prep_pres(self.pres, curr_slide_idx)
        self.update()

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
        if key in ["left", "up", "backspace", "delete", "h", "k"]:
            slide_direction = -1
        elif key in ["right", "down", " ", "j", "l"]:
            slide_direction = 1
        elif key in ["q", "Q"]:
            lookatme.contrib.shutdown_contribs()
            raise urwid.ExitMainLoop()
        elif key == "r":
            self.reload()

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
            return

    def run(self):
        self.loop.run()



def create_tui(pres, start_slide=0):
    """Run the provided presentation

    :param int start_slide: 0-based slide index
    """
    tui = MarkdownTui(pres, palette, start_slide)
    return tui
