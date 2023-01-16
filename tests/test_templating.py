"""
Test the limited templating functionality for rendering slides to
html.
"""


import inspect
import json


import pytest


import lookatme.templating as templating


def test_basic_templating(tmpdir):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable}} {{variable}}

    {{variable}}
    """
    )

    md_path = tmpdir / "test.md"
    with open(md_path, "w") as f:
        f.write(template_data)

    context = {"variable": "A"}
    res = templating.render(md_path, context)

    assert res == template_data.replace("{{variable}}", "A")


def test_basic_templating_errors(tmpdir):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable}} {{dne1}}

    {{dne2}}
    """
    )

    md_path = tmpdir / "test.md"
    with open(md_path, "w") as f:
        f.write(template_data)

    context = {"variable": "A"}
    with pytest.raises(ValueError) as e_info:
        templating.render(md_path, context)

    assert "dne1" in str(e_info.value)
    assert "dne2" in str(e_info.value)


def test_json_filter(tmpdir):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable|json}} {{variable}}
    """
    )

    md_path = tmpdir / "test.md"
    with open(md_path, "w") as f:
        f.write(template_data)

    context = {"variable": "A"}
    res = templating.render(md_path, context)
    assert res == (
        template_data.replace(
            "{{variable|json}}", json.dumps(context["variable"])
        ).replace("{{variable}}", context["variable"])
    )
