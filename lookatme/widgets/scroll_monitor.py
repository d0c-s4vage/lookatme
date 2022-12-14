import urwid


from lookatme.widgets.scrollbar import Scrollbar


class ScrollMonitor(urwid.Frame):
    def __init__(self, main_widget: urwid.Widget, scrollbar: Scrollbar):
        self.main_widget = main_widget
        self.scrollbar = scrollbar
        super().__init__(self.main_widget)

    def render(self, size, focus: bool = True):
        if not self.scrollbar.should_display(size):
            return super().render(size, focus)

        width, height = size

        main_canvas = super().render((width - 1, height), focus)
        if not isinstance(main_canvas, urwid.CompositeCanvas):
            main_canvas = urwid.CompositeCanvas(main_canvas)

        scroll_canvas = self.scrollbar.render((1, height), focus)
        if not isinstance(scroll_canvas, urwid.CompositeCanvas):
            scroll_canvas = urwid.CompositeCanvas(scroll_canvas)

        return urwid.CanvasJoin(
            [
                (main_canvas, None, True, main_canvas.cols()),
                (scroll_canvas, None, False, scroll_canvas.cols()),
            ]
        )
