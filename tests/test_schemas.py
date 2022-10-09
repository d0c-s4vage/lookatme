"""
Test tha lookatme YAML schemas behave as expected
"""


import datetime

import marshmallow.exceptions
import pytest
from marshmallow import Schema, fields

import lookatme.schemas as schemas


def test_meta_schema():
    """Test the meta schema"""
    title = "TITLE"
    author = "AUTHOR"
    date = "2019-01-01"
    yaml_text = f"""
title: {title}
author: {author}
date: {date}
    """

    schema = schemas.MetaSchema().loads(yaml_text)
    assert schema["title"] == title
    assert schema["author"] == author
    assert schema["date"] == "2019-01-01"


def test_meta_schema_allowed_extra_top_level():
    """Test that extra top-level fields are allowed in the metadata. A separate
    test will test that the style metadata is strictly validated.
    """
    """Test the meta schema
    """
    title = "TITLE"
    author = "AUTHOR"
    date = "2019-01-01"
    yaml_text = f"""
title: {title}
author: {author}
date: {date}
tags: [t1, t2, t3]
status: status_str
    """

    schema = schemas.MetaSchema().loads(yaml_text)
    assert schema["title"] == title
    assert schema["author"] == author
    assert schema["date"] == "2019-01-01"
    assert schema["tags"] == ["t1", "t2", "t3"]
    assert schema["status"] == "status_str"


def test_meta_schema_strict_style_validation():
    """Test that the style schema is STRICTLY validated. Not having this will
    make it hard to debug why mistakes in style names aren't having the desired
    effect on lookatme. We want the user to know what fields they got wrong
    in the style.
    """
    """Test the meta schema
    """
    title = "TITLE"
    author = "AUTHOR"
    date = "2019-01-01"
    yaml_text = f"""
title: {title}
author: {author}
date: {date}
styles:
  invalid: 100
    """
    with pytest.raises(marshmallow.exceptions.ValidationError) as exc_info:
        schemas.MetaSchema().loads(yaml_text)

    assert exc_info.value.messages_dict == {"styles": {"invalid": ["Unknown field."]}}


def _validate_field_recursive(path, field, gend_value):
    """Only validate the leaf nodes - we want *specific* values that have
    changed!
    """
    if isinstance(field, Schema):
        for field_name, sub_field in field.fields.items():
            _validate_field_recursive(
                f"{path}.{field_name}", sub_field, gend_value[field_name]
            )
    elif isinstance(field, fields.Nested):
        if field.dump_default is None:
            nested_field = field.nested()  # type: ignore
            _validate_field_recursive(path, nested_field, gend_value)
        else:
            for field_name, sub_field in field.dump_default.items():
                _validate_field_recursive(
                    f"{path}.{field_name}", sub_field, gend_value[field_name]
                )
    elif isinstance(field, fields.Field):
        if isinstance(field.dump_default, datetime.datetime):
            return
        assert field.dump_default == gend_value, f"Default value not correct at {path}"
    elif isinstance(field, dict):
        for field_name, sub_field in field.items():
            _validate_field_recursive(
                f"{path}.{field_name}", sub_field, gend_value[field_name]
            )
    else:
        assert field == gend_value, f"Default value not correct at {path}"


def test_sanity_check_that_errors_are_detected():
    """Perform a sanity check that we can actually catch errors in generating
    the default schema values.
    """
    schema = schemas.MetaSchema()

    # force a discrepancy in the
    gend_default = schemas.MetaSchema().dump(None)
    gend_default["styles"]["padding"]["left"] = 100

    with pytest.raises(AssertionError) as excinfo:
        _validate_field_recursive(
            "__root__.styles", schema.fields["styles"], gend_default["styles"]
        )
    assert "Default value not correct at __root__.styles.padding" in str(excinfo)


def test_styles_defaults():
    """Ensure that style value defaults are generated correctly"""
    schema = schemas.MetaSchema()
    gend_default = schemas.MetaSchema().dump(None)
    _validate_field_recursive(
        "__root__.styles", schema.fields["styles"], gend_default["styles"]
    )


def test_meta_defaults():
    """Test that the default values in the schema are actually used"""
    schema = schemas.MetaSchema()
    gend_default = schemas.MetaSchema().dump(None)
    _validate_field_recursive("__root__", schema, gend_default)
