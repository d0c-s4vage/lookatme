"""
"""


import copy
import contextlib
from typing import Union, Tuple
import urwid


import lookatme.config
import lookatme.utils as utils
from lookatme.widgets.clickable_text import ClickableText


class TagDisplay:
    INLINE = "inline"
    BLOCK = "block"


class Context:
    """
    """

    def __init__(self, loop):
        self.container_stack = []
        self.loop = loop
        self.tag_stack = []
        self.spec_stack = []
        self.inline_render_results = []
        self.level = 0

        self._log = lookatme.config.LOG.getChild("ctx")

    @contextlib.contextmanager
    def level_inc(self):
        """
        """
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1

    def log_debug(self, msg):
        indent = "  " * self.level
        self._log.debug(indent + msg)


    def inline_push(self, inline_result):
        """Push a new inline render result onto the stack
        """
        self.inline_render_results.append(inline_result)

    def inline_clear(self):
        """Clear the inline rendered results
        """
        self.inline_render_results.clear()

    def get_inline_markup(self):
        """Return the current inline markup, ignoring any widgets that may
        have made it in
        """
        res = filter(
            lambda x: not isinstance(x, urwid.Widget),
            self.inline_render_results
        )
        return list(res)

    def get_inline_widgets(self):
        """Return the results of any inline rendering that has occurred in
        Widget form. The conversion here is necessary since inline rendering
        functions often produce urwid Text Markup instead of widgets, which
        need to be converted to ClickableText.
        """
        res = []
        curr_text_markup = []
        for render_res in self.inline_render_results:
            if isinstance(render_res, urwid.Widget):
                if len(curr_text_markup) > 0:
                    res.append(ClickableText(curr_text_markup))
                    curr_text_markup = []
                res.append(render_res)
            if (
                isinstance(render_res, str) or
                (isinstance(render_res, (tuple|list)) and len(render_res) == 2)
            ):
                curr_text_markup.append(render_res)

        if len(curr_text_markup) > 0:
            res.append(ClickableText(curr_text_markup))

        res = [urwid.AttrMap(x, {None: self.spec_text}) for x in res]

        return res
    
    def inline_convert_all_to_widgets(self):
        self.inline_render_results = self.inline_widgets_consumed
    inline_flush = inline_convert_all_to_widgets
    
    @property
    def inline_markup_consumed(self):
        """Return and clear the inline markup
        """
        res = self.get_inline_markup()
        self.log_debug(">>>> InlineMarkup: {!r}".format(res))
        self.inline_clear()
        return res
    
    @property
    def inline_widgets_consumed(self):
        """Return and clear the inline widgets
        """
        res = self.get_inline_widgets()
        self.log_debug(">>>> InlineWidgets: {!r}".format(res))
        self.inline_clear()
        return res

    @property
    def is_literal(self):
        # walk the tag_stack backwards and see if we are in any <pre> elements
        for tag_name in reversed(self.tag_stack):
            if tag_name == "pre":
                return True
        return False

    def tag_push(self, new_tag, spec=None, text_only_spec=False, display=TagDisplay.INLINE):
        """Push a new tag name onto the stack
        """
        if display == TagDisplay.BLOCK:
            self.inline_flush()

        if spec is not None:
            self.spec_push(spec, text_only=text_only_spec)
        self.tag_stack.append((new_tag, spec is not None, display))

    def tag_pop(self):
        """Pop the most recent tag off of the tag stack
        """
        if len(self.tag_stack) == 0:
            raise ValueError("Tried to pop off the tag stack one too many times")

        popped_tag, had_spec, display = self.tag_stack.pop()

        if had_spec:
            self.spec_pop()

        if display == TagDisplay.BLOCK:
            self.log_debug("FLUSHING INLINE (BLOCK): {!r}".format(popped_tag))
            self.inline_flush()

        return (popped_tag, had_spec, display)

    @property
    def tag(self):
        if len(self.tag_stack) == 0:
            return None
        return self.tag_stack[-1][0]

    def container_push(self, new_item):
        """Push to the stack and propagate metadata
        """
        if len(self.container_stack) > 0:
            self._propagate_meta(self.container, new_item)
        self.container_stack.append(new_item)

    def container_pop(self):
        """Pop the last element off the stack. Returns the popped widget
        """
        if len(self.container_stack) == 0:
            raise ValueError("Tried to pop off the widget stack one too many times")
        return self.container_stack.pop()

    @property
    def container(self):
        """Return the current container
        """
        if len(self.container_stack) > 0:
            return self.container_stack[-1]
        return None

    @property
    def container_last(self):
        if self.container is None:
            return None

        cont_children = []
        if hasattr(self.container, "body"):
            cont_children = self.container.body
        elif hasattr(self.container, "contents"):
            cont_children = self.container.contents

        if len(cont_children) == 0:
            return None
        return cont_children[-1]

    @contextlib.contextmanager
    def use_container(self, new_container):
        """Ensure that the container is pushed/popped correctly
        """
        self.container_push(new_container)
        try:
            yield
        finally:
            self.container_pop()
    
    def spec_push(self, new_spec, text_only=False):
        """Push a new AttrSpec onto the spec_stack
        """
        self.spec_stack.append((new_spec, text_only))
    
    def spec_pop(self):
        """Push a new AttrSpec onto the spec_stack
        """
        if len(self.spec_stack) == 0:
            raise ValueError("Tried to pop off the spec stack one too many times")
        return self.spec_stack.pop()
    
    @property
    def spec_general(self):
        """Return the current fully resolved current AttrSpec
        """
        return utils.spec_from_stack(
            self.spec_stack,
            lambda s, text_only: not text_only,
        )
    
    @property
    def spec_text(self):
        """
        """
        return utils.spec_from_stack(
            self.spec_stack,
            # include all of the specs!
            lambda s, text_only: True,
        )
    
    @contextlib.contextmanager
    def use_spec(self, new_spec):
        """Ensure that specs are pushed/popped correctly
        """
        self.spec_push(new_spec)
        try:
            yield
        finally:
            self.spec_pop()

    # -------------------------------------------------------------------------
    # private functions -------------------------------------------------------
    # -------------------------------------------------------------------------

    def _propagate_meta(self, item1, item2):
        """Copy the metadata from item1 to item2
        """
        meta = getattr(item1, "meta", {})
        existing_meta = getattr(item2, "meta", {})
        new_meta = copy.deepcopy(meta)
        new_meta.update(existing_meta)
        setattr(item2, "meta", new_meta)
