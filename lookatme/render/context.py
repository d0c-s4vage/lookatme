"""
"""


import copy
import contextlib


import lookatme.utils as utils


class Context:
    """
    """

    def __init__(self, loop):
        self.container_stack = []
        self.loop = loop
        self.spec_stack = []
        self.tag_stack = []
        self.literal_text_count = 0

    def literal_push(self):
        self.literal_text_count += 1

    def literal_pop(self):
        if self.literal_text_count == 0:
            raise ValueError("Tried to pop off the literal text one too many times")
        self.literal_text_count -= 1

    @property
    def is_literal(self):
        return self.literal_text_count > 0

    def tag_push(self, new_tag, spec=None):
        """Push a new tag name onto the stack
        """
        if spec is not None:
            self.spec_push(spec)
        self.tag_stack.append((new_tag, spec is not None))

    def tag_pop(self):
        """Pop the most recent tag off of the tag stack
        """
        if len(self.tag_stack) == 0:
            raise ValueError("Tried to pop off the tag stack one too many times")
        popped_tag, had_spec = self.tag_stack.pop()
        if had_spec:
            self.spec_pop()
        return (popped_tag, had_spec)

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

    @contextlib.contextmanager
    def use_container(self, new_container):
        """Ensure that the container is pushed/popped correctly
        """
        self.container_push(new_container)
        try:
            yield
        finally:
            self.container_pop()
    
    def spec_push(self, new_spec):
        """Push a new AttrSpec onto the spec_stack
        """
        self.spec_stack.append(new_spec)
    
    def spec_pop(self):
        """Push a new AttrSpec onto the spec_stack
        """
        if len(self.spec_stack) == 0:
            raise ValueError("Tried to pop off the spec stack one too many times")
        return self.spec_stack.pop()
    
    @property
    def spec(self):
        """Return the current fully resolved current AttrSpec
        """
        return utils.spec_from_stack(self.spec_stack)
    
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
