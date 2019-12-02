"""
Test tha lookatme YAML schemas behave as expected
"""


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
