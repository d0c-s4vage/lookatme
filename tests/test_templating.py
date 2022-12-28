"""
Test the limited templating functionality for rendering slides to
html.
"""


import inspect
import json


import pytest


import lookatme.render.html.templating as templating


def test_basic_templating(mocker):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable}} {{variable}}

    {{variable}}
    """
    )

    mocker.patch(
        "lookatme.render.html.templating.get_template_data",
        return_value=template_data,
    )

    context = {"variable": "A"}
    res = templating.render("some_template.template.html", context)

    assert res == template_data.replace("{{variable}}", "A")


def test_basic_templating_errors(mocker):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable}} {{dne1}}

    {{dne2}}
    """
    )

    mocker.patch(
        "lookatme.render.html.templating.get_template_data",
        return_value=template_data,
    )

    context = {"variable": "A"}
    with pytest.raises(ValueError) as e_info:
        templating.render("some_template.template.html", context)

    assert "dne1" in str(e_info.value)
    assert "dne2" in str(e_info.value)


def test_json_filter(mocker):
    template_data = inspect.cleandoc(
        r"""
    This is a test {{variable|json}} {{variable}}
    """
    )

    mocker.patch(
        "lookatme.render.html.templating.get_template_data",
        return_value=template_data,
    )

    context = {"variable": "A"}
    res = templating.render("some_template.template.html", context)
    assert res == (
        template_data.replace(
            "{{variable|json}}", json.dumps(context["variable"])
        ).replace("{{variable}}", context["variable"])
    )
