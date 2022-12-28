"""
"""

from __future__ import annotations


import contextlib
import copy
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import urwid

import lookatme.config
import lookatme.utils as utils
from lookatme.widgets.clickable_text import ClickableText
from lookatme.render.token_iterator import TokenIterator


@dataclass
class ContainerInfo:
    container: urwid.Widget
    meta: Dict[str, Any]
    source_token: Optional[Dict]


class Context:
    """ """

    def __init__(self, loop: Optional[urwid.MainLoop]):
        self.loop = loop

        self.container_stack: List[ContainerInfo] = []
        self.tag_stack: List[Tuple[str, Dict, bool]] = []
        self.spec_stack = []
        self.source_stack = []
        self.inline_render_results = []
        self.token_stack: List[TokenIterator] = []
        self._unwind_tokens: List[Tuple[bool, Dict]] = []
        self.validation_states = {}

        self.level = 0
        self.in_new_block = True

        self._log = lookatme.config.get_log()

    def clone(self) -> Context:
        """Create a new limited clone of the current context.

        The only data that is actually cloned is the source and spec stacks.
        """
        res = Context(self.loop)
        res.source_stack = list(self.source_stack)
        res.spec_stack = list(self.spec_stack)
        res.token_stack = list(self.token_stack)
        res.container_stack = list(self.container_stack)

        return res

    def _validate_empty_list(self, stack_name: str, stack: List[Any]):
        if len(stack) == 0:
            return

        raise RuntimeError(
            "The {} stack did not return to empty, {} items remaining".format(
                stack_name, len(stack)
            )
        )

    def _set_validation_state(self, name: str, container: Any):
        self.validation_states[name] = (container, len(container))

    def clean_state_snapshot(self):
        self._set_validation_state("container", self.container_stack)
        self._set_validation_state("tag", self.tag_stack)
        self._set_validation_state("spec", self.spec_stack)
        self._set_validation_state("source", self.source_stack)
        self._set_validation_state("tokens", self.token_stack)
        self._set_validation_state("inline render results", self.inline_render_results)

    def clean_state_validate(self):
        """Validate that all stacks are empty, that everything unwound correctly"""
        errors = []
        for list_name, (container, expected) in self.validation_states.items():
            if len(container) != expected:
                errors.append(
                    "{} should have been {}, was {}".format(
                        list_name,
                        expected,
                        len(container),
                    )
                )

        if self.level != 0:
            errors.append("Context level did not return to 0, is {}".format(self.level))

        if errors:
            raise RuntimeError(
                "Context did not unwind correctly:\n\n{}".format(
                    "\n".join("    " + error for error in errors)
                )
            )

    def fake_token(self, type: str, **kwargs) -> Dict:
        res = {"type": type, **kwargs}
        res["map"] = self.tokens.curr["map"]
        self.tokens._handle_unwind(res)
        return res

    @property
    def source(self) -> str:
        """Return the current markdown source"""
        if not self.source_stack:
            raise ValueError("No source has been set!")
        return self.source_stack[-1]

    def source_push(self, new_source: str):
        """Push new markdown source onto the source stack"""
        self.source_stack.append(new_source)

    def source_pop(self) -> str:
        """Pop the latest source off of the source stack"""
        if not self.source_stack:
            raise ValueError("Tried to pop off the source_stack one too many times")
        return self.source_stack.pop()

    def source_get_token_lines(
        self,
        token: Dict,
        extra: int = 5,
        with_lines: bool = True,
        with_marker: bool = True,
    ) -> List[str]:
        lines = self.source.split("\n")
        range_start, range_end = token["map"]

        before_extra = range_start - max(range_start - extra, 0)
        after_extra = min(len(lines), range_end + extra) - range_end

        source_lines = self.source.split("\n")[
            range_start - before_extra : range_end + after_extra
        ]

        if with_lines:
            max_line_len = len(str(range_end + extra))
            for idx, line in enumerate(source_lines):
                source_lines[idx] = "{{line_no:{}}} {{line}}".format(
                    max_line_len
                ).format(
                    line_no=range_start - before_extra + idx + 1,
                    line=line,
                )

        if with_marker:
            for idx, line in enumerate(source_lines):
                if idx >= before_extra and idx < len(source_lines) - after_extra:
                    source_lines[idx] = line = "  HERE->  " + line
                else:
                    source_lines[idx] = line = "          " + line

        return source_lines

    def _create_unwind_tokens(self, from_idx: int = 0) -> List[Dict]:
        _, latest_map_end = self.tokens.curr["map"]
        latest_map = [latest_map_end - 1, latest_map_end]

        res = []

        idx = 0
        curr_inlines = []
        while idx < len(self._unwind_tokens):
            is_inline, token = self._unwind_tokens[idx]
            idx += 1
            token["map"] = latest_map

            if is_inline:
                curr_inlines.append(token)
                continue

            if curr_inlines:
                res.append(
                    {
                        "type": "inline",
                        "map": latest_map,
                        "children": curr_inlines,
                    }
                )
                curr_inlines.clear()

            res.append(token)

        if curr_inlines:
            res.append(
                {
                    "type": "inline",
                    "map": latest_map,
                    "children": curr_inlines,
                }
            )

        return list(reversed(res))

    @property
    def unwind_tokens(self) -> List[Dict]:
        """Generate a list of unwind (close) tokens from the token iterators
        in the stack
        """
        return self._create_unwind_tokens()

    def unwind_tokens_from(self, bookmark: int) -> List[Dict]:
        return self._create_unwind_tokens(bookmark)

    @property
    def unwind_bookmark(self) -> int:
        return len(self._unwind_tokens)

    @property
    def unwind_tokens_consumed(self) -> List[Dict]:
        """Generate a list of unwind (close) tokens from the token iterators
        in the stack
        """
        res = self.unwind_tokens
        self._unwind_tokens.clear()
        return res

    @property
    def tokens(self) -> TokenIterator:
        """Return the current token iterator"""
        if not self.token_stack:
            raise ValueError("Attempted to fetch tokens without providing any")
        return self.token_stack[-1]

    def tokens_push(self, tokens: List[Dict], inline: bool = False):
        """ """
        self.token_stack.append(
            TokenIterator(copy.deepcopy(tokens), self._unwind_tokens, inline)
        )

    def tokens_pop(self):
        """ """
        return self.token_stack.pop()

    @contextlib.contextmanager
    def use_tokens(self, tokens, inline: bool = False):
        """Create a context manager for pushing/popping tokens via a with block"""
        self.tokens_push(tokens, inline)
        yield
        # do not pop tokens when an exception occurrs! We want to have full
        # context when handlingn errors!
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
        yield
        # do not pop tokens when an exception occurrs! We want to have full
        # context when handlingn errors!
        self.level -= 1

    def log_debug(self, msg):
        indent = "  " * self.level
        self._log.debug(indent + msg)

    def inline_push(
        self,
        inline_result: Union[urwid.Widget, str, Tuple[Optional[urwid.AttrSpec], str]],
    ):
        """Push a new inline render result onto the stack. Either a widget, or
        text markup
        """
        if isinstance(inline_result, str) and len(inline_result) == 0:
            return
        if isinstance(inline_result, tuple) and len(inline_result) == 2:
            if len(inline_result[1]) == 0:
                return
            if inline_result[0] is None:
                inline_result = inline_result[1]

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
                isinstance(render_res, (tuple, list)) and len(render_res) == 2
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
        self.inline_clear()
        return res

    @property
    def inline_widgets_consumed(self):
        """Return and clear the inline widgets"""
        res = self.get_inline_widgets()
        self.inline_clear()
        return res

    @property
    def is_literal(self):
        return self.tag_is_ancestor("pre")

    def tag_is_ancestor(self, ancestor_tag_name: str) -> bool:
        for tag_name, _, _ in reversed(self.tag_stack):
            if tag_name == ancestor_tag_name:
                return True
        return False

    def tag_push(self, new_tag: str, token: Dict, spec=None, text_only_spec=False):
        """Push a new tag name onto the stack"""
        if spec is not None:
            self.spec_push(spec, text_only=text_only_spec)
        self.tag_stack.append((new_tag, token, spec is not None))

    def tag_pop(self):
        """Pop the most recent tag off of the tag stack"""
        if not self.tag_stack:
            raise ValueError("Tried to pop off the tag stack one too many times")

        popped_tag, _, had_spec = self.tag_stack.pop()

        if had_spec:
            self.spec_pop()

        return (popped_tag, had_spec)

    @property
    def tag(self):
        if self.tag_stack:
            return None
        return self.tag_stack[-1][0]

    @property
    def tag_token(self) -> Dict:
        if not self.tag_stack:
            raise ValueError("Tried to get the token for a non-existent tag")
        return self.tag_stack[-1][1]

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

        new_info = ContainerInfo(
            container=new_item, meta=new_meta, source_token=self.tokens.curr
        )
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
        yield
        # do not pop tokens when an exception occurrs! We want to have full
        # context when handlingn errors!
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
        yield
        # do not pop tokens when an exception occurrs! We want to have full
        # context when handlingn errors!
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

    def spec_peek(self) -> urwid.AttrSpec:
        """Return the most recent spec, or None"""
        if not self.spec_stack:
            raise ValueError("Tried to pop off the spec stack one too many times")
        return self.spec_stack[-1][0]

    @property
    def spec_general(self) -> Union[None, urwid.AttrSpec]:
        """Return the current fully resolved current AttrSpec"""
        return utils.spec_from_stack(
            self.spec_stack,
            lambda s, text_only: not text_only,
        )

    @property
    def spec_text(self) -> urwid.AttrSpec:
        """ """
        return utils.spec_from_stack(
            self.spec_stack,
            # include all of the specs!
            lambda s, text_only: True,
        )

    def spec_text_with(self, other_spec: Union[None, urwid.AttrSpec]) -> urwid.AttrSpec:
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
        yield
        # do not pop tokens when an exception occurrs! We want to have full
        # context when handlingn errors!
        if new_spec is not None:
            self.spec_pop()
