"""
"""


import contextlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import urwid

import lookatme.config
import lookatme.utils as utils
from lookatme.widgets.clickable_text import ClickableText


@dataclass
class ContainerInfo:
    container: urwid.Widget
    meta: Dict[str, Any]


class TokenIterator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.idx = 0

    def peek(self) -> Optional[Dict]:
        """Return the next token in the token stream, or None if it does
        not exist
        """
        if self.idx >= len(self.tokens):
            return None
        return self.tokens[self.idx]

    def next(self):
        token = self.peek()
        if token is not None:
            self.idx += 1
        return token

    def __iter__(self):
        return self

    def __next__(self):
        token = self.next()
        if token is None:
            raise StopIteration
        return token


class Context:
    """ """

    def __init__(self, loop):
        self.container_stack: List[ContainerInfo] = []
        self.loop = loop
        self.tag_stack = []
        self.spec_stack = []
        self.inline_render_results = []
        self.level = 0
        self.in_new_block = True

        self.token_stack: List[TokenIterator] = []

        self._log = lookatme.config.get_log()

    @property
    def tokens(self) -> TokenIterator:
        """Return the current token iterator"""
        if not self.token_stack:
            raise ValueError("Attempted to fetch tokens without providing any")
        return self.token_stack[-1]

    @property
    def token_next(self):
        """Return the next token in the token iterator, advancing the iterator"""
        return self.tokens.next()

    def tokens_push(self, tokens: List[Dict]):
        """ """
        self.token_stack.append(TokenIterator(tokens))

    def tokens_pop(self):
        """ """
        self.token_stack.pop()

    @contextlib.contextmanager
    def use_tokens(self, tokens):
        """Create a context manager for pushing/popping tokens via a with block"""
        self.tokens_push(tokens)
        try:
            yield
        finally:
            self.tokens_pop()

    def ensure_new_block(self):
        """Ensure that we are in a new block"""
        if not self.in_new_block:
            utils.pile_or_listbox_add(self.container, self.inline_widgets_consumed)
            self.widget_add(self.wrap_widget(urwid.Divider()))

        self.in_new_block = True

    def widget_add(
        self, w: Union[List[urwid.Widget], urwid.Widget], wrap: Optional[bool] = False
    ):
        """Add the provided widget to the current container."""
        if wrap:
            if isinstance(w, (list, tuple)):
                w = [self.wrap_widget(x) for x in w]
            else:
                w = self.wrap_widget(w)

        self.in_new_block = False
        utils.pile_or_listbox_add(self.container, w)

    @contextlib.contextmanager
    def level_inc(self):
        """ """
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1

    def log_debug(self, msg):
        indent = "  " * self.level
        self._log.debug(indent + msg)

    def inline_push(
        self, inline_result: Union[urwid.Widget, str, Tuple[urwid.AttrSpec, str]]
    ):
        """Push a new inline render result onto the stack. Either a widget, or
        text markup
        """
        if isinstance(inline_result, str) and len(inline_result) == 0:
            return
        if isinstance(inline_result, tuple) and len(inline_result) == 2:
            if len(inline_result[1]) == 0:
                return

        self.in_new_block = False
        self.inline_render_results.append(inline_result)

    def inline_clear(self):
        """Clear the inline rendered results"""
        self.inline_render_results.clear()

    def get_inline_markup(self):
        """Return the current inline markup, ignoring any widgets that may
        have made it in
        """
        res = filter(
            lambda x: not isinstance(x, urwid.Widget), self.inline_render_results
        )
        return list(res)

    def wrap_widget(
        self, w: urwid.Widget, spec: Optional[urwid.AttrSpec] = None
    ) -> urwid.Widget:
        """Wrap the provided widget with an AttrMap that will apply
        the current styling to the entire widget (using spec_general)
        """
        if spec is None:
            spec = self.spec_general
        return urwid.AttrMap(w, {None: spec})

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
                if curr_text_markup:
                    res.append(ClickableText(curr_text_markup))
                    curr_text_markup = []
                res.append(render_res)
            if isinstance(render_res, str) or (
                isinstance(render_res, (tuple | list)) and len(render_res) == 2
            ):
                curr_text_markup.append(render_res)

        if len(curr_text_markup) > 0:
            res.append(ClickableText(curr_text_markup))

        # res = [urwid.AttrMap(x, {None: self.spec_text}) for x in res]

        return res

    def inline_flush(self):
        """Add all inline widgets to the current container"""
        self.widget_add(self.inline_widgets_consumed)

    def inline_convert_all_to_widgets(self):
        self.inline_render_results = self.inline_widgets_consumed

    @property
    def inline_markup_consumed(self):
        """Return and clear the inline markup"""
        res = self.get_inline_markup()
        self.log_debug(">>>> InlineMarkup: {!r}".format(res))
        self.inline_clear()
        return res

    @property
    def inline_widgets_consumed(self):
        """Return and clear the inline widgets"""
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

    def tag_push(self, new_tag, spec=None, text_only_spec=False):
        """Push a new tag name onto the stack"""
        if spec is not None:
            self.spec_push(spec, text_only=text_only_spec)
        self.tag_stack.append((new_tag, spec is not None))

    def tag_pop(self):
        """Pop the most recent tag off of the tag stack"""
        if not self.tag_stack:
            raise ValueError("Tried to pop off the tag stack one too many times")

        popped_tag, had_spec = self.tag_stack.pop()

        if had_spec:
            self.spec_pop()

        return (popped_tag, had_spec)

    @property
    def tag(self):
        if self.tag_stack:
            return None
        return self.tag_stack[-1][0]

    @property
    def meta(self) -> Dict[Any, Any]:
        """Return metadata associated with the current container, or None
        if the current container is None.
        """
        if not self.container_stack:
            raise ValueError("Tried to get meta with no containers!")

        return self.container_stack[-1].meta

    def container_push(
        self,
        new_item: urwid.Widget,
        is_new_block: bool,
        custom_add: Optional[urwid.Widget] = None,
    ):
        """Push to the stack and propagate metadata"""
        if custom_add is not None:
            custom_add = self.wrap_widget(custom_add)
        else:
            new_item = self.wrap_widget(new_item)

        self.log_debug("Container: {!r}".format(new_item))
        new_meta = {}
        if self.container_stack:
            new_meta.update(self.meta)
            self.inline_flush()

            if custom_add is None:
                utils.pile_or_listbox_add(self.container, new_item)
            else:
                utils.pile_or_listbox_add(self.container, custom_add)

        elif self.inline_render_results:
            raise Exception("How do you have render results with no containers?")

        new_info = ContainerInfo(container=new_item, meta=new_meta)
        self.container_stack.append(new_info)
        self.in_new_block = is_new_block

    def container_pop(self) -> ContainerInfo:
        """Pop the last element off the stack. Returns the popped widget"""
        if not self.container_stack:
            raise ValueError("Tried to pop off the widget stack one too many times")

        self.inline_flush()
        return self.container_stack.pop()

    @property
    def container(self) -> urwid.Widget:
        """Return the current container"""
        if not self.container_stack:
            raise ValueError("Tried to get container with no containers")
        return self.container_stack[-1].container

    #     @property
    #     def container_last(self):
    #         if self.container is None:
    #             return None
    #
    #         cont_children = []
    #         if hasattr(self.container, "body"):
    #             cont_children = self.container.body
    #         elif hasattr(self.container, "contents"):
    #             cont_children = self.container.contents
    #
    #         if len(cont_children) == 0:
    #             return None
    #         return cont_children[-1]

    @contextlib.contextmanager
    def use_container(
        self,
        new_container: urwid.Widget,
        is_new_block: bool,
        custom_add: Optional[urwid.Widget] = None,
    ):
        """Ensure that the container is pushed/popped correctly"""
        self.container_push(new_container, is_new_block, custom_add)
        try:
            yield
        finally:
            self.container_pop()

    @contextlib.contextmanager
    def use_container_tmp(self, new_container: urwid.Widget):
        """Swap out the entire container stack for a new one with the
        new container as the only item, while keeping spec and tag stacks
        """
        tmp_inline_render_results = self.inline_render_results
        tmp_container_stack = self.container_stack
        tmp_in_new_block = self.in_new_block

        self.inline_render_results = []
        self.container_stack = []

        self.container_push(new_container, is_new_block=True)
        try:
            yield
        finally:
            self.container_pop()
            self.inline_render_results = tmp_inline_render_results
            self.container_stack = tmp_container_stack
            self.in_new_block = tmp_in_new_block

    def spec_push(self, new_spec, text_only=False):
        """Push a new AttrSpec onto the spec_stack"""
        self.spec_stack.append((new_spec, text_only))

    def spec_pop(self):
        """Push a new AttrSpec onto the spec_stack"""
        if not self.spec_stack:
            raise ValueError("Tried to pop off the spec stack one too many times")
        return self.spec_stack.pop()

    @property
    def spec_general(self) -> Union[None, urwid.AttrSpec]:
        """Return the current fully resolved current AttrSpec"""
        return utils.spec_from_stack(
            self.spec_stack,
            lambda s, text_only: not text_only,
        )

    @property
    def spec_text(self):
        """ """
        return utils.spec_from_stack(
            self.spec_stack,
            # include all of the specs!
            lambda s, text_only: True,
        )

    def spec_text_with(
        self, other_spec: Union[None, urwid.AttrSpec]
    ) -> Union[None, urwid.AttrSpec]:
        if other_spec is None:
            return self.spec_text

        return utils.spec_from_stack(
            [(self.spec_text, True), (other_spec, True)],
        )

    @contextlib.contextmanager
    def use_spec(self, new_spec, text_only=False):
        """Ensure that specs are pushed/popped correctly"""
        if new_spec is not None:
            self.spec_push(new_spec, text_only)
        try:
            yield
        finally:
            if new_spec is not None:
                self.spec_pop()
