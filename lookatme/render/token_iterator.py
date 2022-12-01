"""
This module defines the TokenIterator class.
"""

from typing import Any, Callable, List, Dict, Optional, Tuple
import re


class TokenIterator:
    """This clas"""

    def __init__(
        self,
        tokens: List[Dict],
        unwind_tokens: List[Tuple[bool, Dict]],
        inline: bool = False,
    ):
        """Create a new TokenIterator instance that can iterate/work with the
        provided list of tokens.
        """
        self.tokens = tokens
        self.idx = 0
        self.inline = inline
        self.last_map = None

        self._unwind_tokens = unwind_tokens

    def unwind_has_type(self, unwind_type: str) -> bool:
        for _, token in reversed(self._unwind_tokens):
            if token["type"] == unwind_type:
                return True
        return False

    def at_offset(self, idx_offset: int) -> Optional[Dict]:
        if not self.tokens:
            raise ValueError("No tokens")

        target_idx = self.idx + idx_offset
        if not (0 >= target_idx < len(self.tokens)):
            return None

        return self.tokens[target_idx]

    @property
    def curr(self) -> Dict:
        if not self.tokens:
            raise ValueError("No tokens")
        # we haven't started iterating yet
        if self.idx == 0:
            return self.tokens[self.idx]
        return self.tokens[self.idx - 1]

    def peek(self) -> Optional[Dict]:
        if not self.tokens or self.idx >= len(self.tokens):
            return None
        return self.tokens[self.idx]

    def at_offset_v(self, idx_offset: int) -> Dict:
        res = self.at_offset_v(idx_offset)
        if res is None:
            target_idx = self.idx + idx_offset
            raise ValueError(
                "Idx offset {} (idx {}) is outside of range [{},{})".format(
                    idx_offset,
                    target_idx,
                    0,
                    len(self.tokens),
                )
            )

        return res

    def _unwind_index_matching(self, comparator: Callable) -> Optional[int]:
        for idx, unwind_token in enumerate(self._unwind_tokens):
            if comparator(unwind_token):
                return idx
        return None

    def _handle_unwind(self, token: Dict):
        # we need to recurse into all inline tags so that we can create an
        # unwind stack for html elements that may not have been closed.
        #
        # E.g.:
        #
        # <div>           <-- will be a child of an inline token
        # |h1|h2|
        # |--|--|
        # |a |b |
        # </div>          <-- this will be parsed as a new row in the table,
        #
        #         if token["type"] == "inline":
        #             for child_token in (token.get("children", []) or []):
        #                 self._handle_unwind(child_token)

        tmp_unwind_token: Dict[str, Any] = {"unwound_token": token}

        if "_open" in token["type"]:
            close_token_type = token["type"].replace("open", "close")
            tmp_unwind_token["type"] = close_token_type
            self._unwind_tokens.append((self.inline, tmp_unwind_token))
        elif "_close" in token["type"]:
            # remove the first matching unwind token
            remove_idx = self._unwind_index_matching(
                lambda x: x[1]["type"] == token["type"]
            )
            if remove_idx is None:
                return
            del self._unwind_tokens[remove_idx]
        elif token["type"] == "html_inline":
            tag_info = re.match(
                r"<(?P<close>/)?(?P<tag>[a-z0-9-]+)", token["content"], re.IGNORECASE
            )
            if not tag_info:
                return
            info = tag_info.groupdict()
            if info["tag"] == "br":
                return

            if info["close"]:
                remove_idx = self._unwind_index_matching(
                    lambda x: x[1].get("content", "") == token["content"]
                )
                if remove_idx is None:
                    return
                del self._unwind_tokens[remove_idx]
            else:
                tmp_unwind_token["type"] = "html_inline"
                tmp_unwind_token["content"] = "</{}>".format(info["tag"])
                self._unwind_tokens.append((self.inline, tmp_unwind_token))

    def next(self) -> Optional[Dict]:
        if self.idx >= len(self.tokens):
            return None

        token = self.tokens[self.idx]

        if self.last_map is not None and token.get("map", None) is None:
            # set the missing map value to be the last line of the last_map
            token["map"] = [self.last_map[0] - 1, self.last_map[1]]

        self.last_map = token["map"]
        self.idx += 1
        self._handle_unwind(token)

        return token

    def __iter__(self):
        return self

    def __next__(self):
        token = self.next()
        if token is None:
            raise StopIteration
        return token
