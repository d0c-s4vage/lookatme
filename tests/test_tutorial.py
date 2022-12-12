"""
Test tutorial functionality
"""


import inspect

import lookatme.tutorial as tutorial


def test_real_tutorials_exist():
    assert "general" in tutorial.GROUPED_TUTORIALS
    assert "markdown block" in tutorial.GROUPED_TUTORIALS
    assert "markdown inline" in tutorial.GROUPED_TUTORIALS


def test_tutorial_basic(mocker):
    """Test that tutorials work correctly"""
    mocker.patch("lookatme.tutorial.GROUPED_TUTORIALS", {})
    mocker.patch("lookatme.tutorial.NAMED_TUTORIALS", {})

    @tutorial.tutor("category", "name", "contents")
    def some_function():
        pass

    assert "category" in tutorial.GROUPED_TUTORIALS
    assert "name" in tutorial.GROUPED_TUTORIALS["category"]

    category_md = tutorial.get_tutorial_md(["category"])
    assert category_md is not None

    name_md = tutorial.get_tutorial_md(["name"])
    assert name_md is not None

    assert category_md == name_md
    assert "# Category: Name" in category_md
    assert "contents" in category_md


def test_tutor(mocker):
    mocker.patch("lookatme.config.STYLE", {"test": {"test": "hello"}})
    tutor = tutorial.Tutor(
        "name",
        "group",
        "\n".join(
            [
                "<TUTOR:EXAMPLE {hllines=1}>contents</TUTOR:EXAMPLE>",
                "<TUTOR:STYLE>test</TUTOR:STYLE>",
            ]
        ),
        impl_fn=lambda _: 10,
        order=99999,
    )

    md_text = tutor.get_md()

    md_example = "> ~~~markdown {hllines=1}\n> contents\n> ~~~"
    assert md_example in md_text

    md_rendered = "\ncontents"
    assert md_rendered in md_text

    style_yaml = inspect.cleandoc(
        """
        ```yaml
        ---
        styles:
          test:
            test: hello
        ---
        ```
    """
    ).strip()
    assert style_yaml in md_text


def test_tutor_with_gt_in_example():
    tutor = tutorial.Tutor(
        "name",
        "group",
        "<TUTOR:EXAMPLE>> test</TUTOR:EXAMPLE>",
        impl_fn=lambda _: 10,
        order=99999,
    )
    md_text = tutor.get_md()

    md_example = "> ~~~markdown\n> > test\n> ~~~"
    assert md_example in md_text

    md_rendered = "\n> test"
    assert md_rendered in md_text
