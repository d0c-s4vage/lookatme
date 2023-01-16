"""
Test the functionality of the BaseOutputFormat class and related utility functions
"""


import copy
from typing import Any, Dict, Optional, Type


import pytest


import lookatme.output as output
import lookatme.output.base as base


class OutputCtx:
    @property
    def curr_types(self) -> Dict[str, Type[base.BaseOutputFormat]]:
        return base.DEFINED_TYPES

    def new_type(
        self, name, options: Optional[Dict[str, Any]] = None
    ) -> Type[base.BaseOutputFormat]:
        attrs = {
            "NAME": name,
            "DEFAULT_OPTIONS": options,
        }
        return type(f"{name}Class", (base.BaseOutputFormat,), attrs)


@pytest.fixture(scope="function")
def output_ctx():
    defined_types = copy.copy(base.DEFINED_TYPES)
    base.DEFINED_TYPES.clear()

    ctx = OutputCtx()
    try:
        yield ctx
    finally:
        base.DEFINED_TYPES.clear()
        base.DEFINED_TYPES.update(defined_types)


def test_output_type_registration(output_ctx: OutputCtx):
    assert len(output_ctx.curr_types) == 0

    tmp_class = output_ctx.new_type("tmp")

    assert len(output_ctx.curr_types) == 1

    assert tmp_class.NAME in output_ctx.curr_types  # type: ignore
    assert tmp_class == output_ctx.curr_types[tmp_class.NAME]  # type: ignore


def test_output_options_parsing(output_ctx: OutputCtx):
    output_ctx.new_type(
        "tmp",
        {
            "option1": 10,
            "option2": "hello",
            "option3": ["a", "b", "c"],
            "option4": 10.5,
        },
    )

    options = output.parse_options(
        [
            "tmp.option1=3",
            "tmp.option2=hello world",
            "tmp.option3=x,y,z",
            "tmp.option4=99.9",
        ]
    )

    assert options["tmp.option1"] == 3
    assert options["tmp.option2"] == "hello world"
    assert options["tmp.option3"] == ["x", "y", "z"]
    assert options["tmp.option4"] == 99.9

    assert set(output.get_all_options()) == {
        "tmp.option1",
        "tmp.option2",
        "tmp.option3",
        "tmp.option4",
    }
