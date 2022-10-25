"""
Functions and sources for the markdown tutorial slides!
"""

import inspect
import re
from collections import OrderedDict
from typing import Callable, List, Union

import yaml

import lookatme
import lookatme.config as config
import lookatme.utils as utils


class Tutor:
    """A class to handle/process tutorials for specific functionality

    In addition to name, group, and slides content of the tutor, each Tutor
    must also be associated with the implementation.
    """

    def __init__(self, name: str, group: str, slides_md: str, impl_fn: Callable, order: int):
        """Create a new Tutor"""
        self.name = name
        self.group = group
        self.slides_md = inspect.cleandoc(slides_md).strip()
        self.impl_fn = impl_fn
        self.order = order

    def get_md(self) -> str:
        """Get the tutor's markdown text after resolving any special markup
        contained in it.
        """
        tag_handlers = {
            "EXAMPLE": self._handle_show_and_render,
            "STYLE": self._handle_style_yaml,
        }

        res_md = []
        last_idx = 0
        regex = "<(?P<tag>TUTOR:(?P<type>[A-Z_]+))>(?P<inner>.*)</(?P=tag)>"
        for match in re.finditer(regex, self.slides_md, re.MULTILINE | re.DOTALL):
            res_md.append(self.slides_md[last_idx: match.start()])
            match_groups = match.groupdict()
            handler = tag_handlers.get(match_groups["type"], None)
            if handler is None:
                raise ValueError(
                    "No handler defined for 'TUTOR:{}' tags".format(
                        match_groups["type"]
                    )
                )
            res_md.append(handler(match_groups["inner"]))
            last_idx = match.end() + 1

        res_md.append(self.slides_md[last_idx:])

        return "\n\n".join([
            self._get_heading(),
            "".join(res_md),
            self._get_source_note(),
        ])

    def _get_heading(self) -> str:
        return "# {group}: {name}".format(
            group=self.group.title(),
            name=self.name.title(),
        )

    def _get_source_note(self) -> str:
        link = self._get_source_link()
        return "> This is implemented in {}".format(link)

    def _get_source_link(self):
        file_name = inspect.getsourcefile(inspect.unwrap(self.impl_fn))
        if file_name is None:
            return "??"

        relpath = file_name.split("lookatme/", 1)[1]
        _, lineno = inspect.getsourcelines(self.impl_fn)

        version = "v" + lookatme.VERSION

        return "[{module}.{fn_name}]({link})".format(
            module=self.impl_fn.__module__,
            fn_name=self.impl_fn.__qualname__,
            link="https://github.com/d0c-s4vage/lookatme/blob/{version}/{path}#L{lineno}".format(
                version=version,
                path=relpath,
                lineno=lineno,
            )
        )

    def _handle_show_and_render(self, contents) -> str:
        contents = contents.strip()

        markdown_example = "\n".join([
            "~~~markdown",
            contents,
            "~~~",
        ])
        quoted_example = utils.prefix_text(markdown_example, "> ")

        return "\n\n".join([
            "***Markdown***:",
            quoted_example,
            "***Rendered***:",
            contents + "\n",
        ])

    def _handle_style_yaml(self, contents: str) -> str:
        contents = contents.strip()
        style = config.get_style()[contents]
        style = {"styles": {contents: style}}
        return "```yaml\n---\n{style_yaml}---\n```".format(
            style_yaml=yaml.dump(style).encode().decode("unicode-escape"),
        )


GROUPED_TUTORIALS = OrderedDict()
NAMED_TUTORIALS = OrderedDict()


def print_tutorial_help():
    print(inspect.cleandoc("""
        Help for 'lookatme --tutorial'

        Specific tutorials can be run with a comma-separated list of group or
        tutorial names. Below are the groups and tutorial names currently defined.
    """).strip())
    print()

    for group_name, group_tutors in GROUPED_TUTORIALS.items():
        print("  " + group_name)
        for tutor_name in group_tutors.keys():
            print("    " + tutor_name)

    print()
    print(inspect.cleandoc("""
        Substring matching is used to identify tutorials and groups. All matching
        tutorials and groups are then run.

        Examples:
            lookatme --tutorial
            lookatme --tutorial link,table
            lookatme --tutorial general,list
    """).strip())


def tutor(group: str, name: str, slides_md: str, order: int = 99999):
    """Define tutorial slides by using this as a decorator on a function!"""
    def capture_fn(fn):
        tutor = Tutor(name, group, slides_md, fn, order)
        tutor_list = (
            GROUPED_TUTORIALS
            .setdefault(group, OrderedDict())
            .setdefault(name, [])
        )
        tutor_list.append(tutor)
        NAMED_TUTORIALS.setdefault(name, []).append(tutor)
        return fn
    return capture_fn


def pretty_close_match(str1, str2):
    str1 = str1.lower()
    str2 = str2.lower()
    if str1 in str2 or str2 in str1:
        return True


def get_tutors(group_or_tutor: str) -> List[Tutor]:
    for group_name, group_value in GROUPED_TUTORIALS.items():
        if pretty_close_match(group_name, group_or_tutor):
            return list(group_value.values())

    res = []
    for grouped_tutors in GROUPED_TUTORIALS.values():
        for tutor_name, tutor_list in grouped_tutors.items():
            if pretty_close_match(tutor_name, group_or_tutor):
                res.append(tutor_list)

    return res


def _sort_tutors_by_order():
    for group_name, tutors in list(GROUPED_TUTORIALS.items()):
        del GROUPED_TUTORIALS[group_name]
        tutor_list = list(tutors.items())
        tutor_list = list(sorted(
            tutor_list,
            key=lambda x: min(tutor.order for tutor in x[1]),
        ))
        GROUPED_TUTORIALS[group_name] = OrderedDict(tutor_list)


def get_tutorial_md(groups_or_tutors: List[str]) -> Union[None, str]:
    _sort_tutors_by_order()

    tutors = []
    for group_or_tutor in groups_or_tutors:
        tutors += get_tutors(group_or_tutor)

    if len(tutors) == 0:
        return None

    res_slides = []
    for tutor in tutors:
        tutor_md = "\n\n".join(t.get_md() for t in tutor)
        res_slides.append(tutor_md)

    meta = inspect.cleandoc("""
        ---
        title: lookatme Tutorial
        author: lookatme devs
        ---
    """).strip()

    return meta + "\n" + "\n\n---\n\n".join(res_slides) + "\n\n---\n\n# End"
