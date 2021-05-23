"""
Test tha lookatme YAML schemas behave as expected
"""


import datetime
from marshmallow import fields, Schema
import pytest


from lookatme.schemas import *


def test_meta_schema():
    """Test the meta schema
    """
    title = "TITLE"
    author = "AUTHOR"
    date = "2019-01-01"
    yaml_text = f"""
title: {title}
author: {author}
date: {date}
    """

    schema = MetaSchema().loads(yaml_text)
    assert schema["title"] == title
    assert schema["author"] == author
    assert schema["date"].year == 2019
    assert schema["date"].month == 1
    assert schema["date"].day == 1


def _validate_field_recursive(path, field, gend_value):
    """Only validate the leaf nodes - we want *specific* values that have
    changed!
    """
    if isinstance(field, Schema):
        for field_name, sub_field in field.fields.items():
            _validate_field_recursive(path + "." + field_name, sub_field, gend_value[field_name])
    elif isinstance(field, fields.Nested):
        if field.default is None:
            nested_field = field.nested()
            _validate_field_recursive(path, nested_field, gend_value)
        else:
            assert field.default == gend_value, f"Default value not correct at {path}"
    elif isinstance(field, fields.Field):
        if isinstance(field.default, datetime.datetime):
            return
        assert field.default == gend_value, f"Default value not correct at {path}"


def test_sanity_check_that_errors_are_detected():
    """Perform a sanity check that we can actually catch errors in generating
    the default schema values.
    """
    schema = MetaSchema()

    # force a discrepancy in the 
    gend_default = MetaSchema().dump(None)
    gend_default["styles"]["padding"]["left"] = 100

    with pytest.raises(AssertionError) as excinfo:
        _validate_field_recursive("__root__.styles", schema.styles.nested(), gend_default['styles'])
    assert "Default value not correct at __root__.styles.padding" in str(excinfo)


def test_styles_defaults():
    """Ensure that style value defaults are generated correctly
    """
    schema = MetaSchema()
    gend_default = MetaSchema().dump(None)
    _validate_field_recursive("__root__.styles", schema.styles.nested(), gend_default['styles'])


def test_meta_defaults():
    """Test that the default values in the schema are actually used
    """
    schema = MetaSchema()
    gend_default = MetaSchema().dump(None)
    _validate_field_recursive("__root__", schema, gend_default)
