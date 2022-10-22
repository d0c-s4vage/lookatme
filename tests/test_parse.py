"""
This module tests that markdown presentations can be correctly parsed
"""


import datetime

from lookatme.parser import Parser


def test_parse_metadata():
    """Test that metadata can be correctly parsed out of a markdown
    presentation
    """
    title = "Presentation Title"
    date = "September 2, 2022"
    author = "The Author"

    input_data = f"""
---
title: {title}
date: {date}
author: {author}
---
remaining
    """

    parser = Parser()
    input_data, meta = parser.parse_meta(input_data)
    assert input_data.strip() == "remaining"
    assert meta["title"] == title
    assert meta["date"] == "September 2, 2022"
    assert meta["author"] == author


def test_parse_metadata_empty():
    """Test that metadata can be correctly parsed out of a markdown
    presentation
    """
    input_data = """
---
---
remaining
    """

    parser = Parser()
    input_data, meta = parser.parse_meta(input_data)
    assert input_data.strip() == "remaining"
    now = datetime.datetime.now()
    assert meta["title"] == ""
    assert meta["date"] == now.strftime("%Y-%m-%d")
    assert meta["author"] == ""


def test_parse_slides():
    """Test that slide parsing works correctly
    """
    input_data = r"""
# Slide 1

* list
  * item
  * item
  * item

Hello there this is a paragraph

```python
code block
```

---

# Slide 2

More text
    """
    parser = Parser()
    _, slides = parser.parse_slides({}, input_data)
    assert len(slides) == 2


def test_parse_slides_with_progressive_stops_and_hrule_splits():
    """Test that slide parsing works correctly
    """
    input_data = r"""
# Heading

<!-- stop -->

p1

<!-- stop -->

p2

---

# Slide 2

More text
    """
    parser = Parser()
    _, slides = parser.parse_slides({}, input_data)
    assert len(slides) == 4


def test_parse_smart_slides_one_h1():
    """Test that slide smart splitting works correctly
    """
    input_data = r"""
# Heading Title

## Heading 2

some text

## Heading 3

more text

## Heading 4

### Sub heading

#### Sub Heading
    """
    parser = Parser()
    meta = {"title": ""}
    _, slides = parser.parse_slides(meta, input_data)
    assert len(slides) == 4
    assert meta["title"] == "Heading Title"


def test_parse_smart_slides_multiple_h2():
    """Test that slide smart splitting works correctly
    """
    input_data = r"""
## Heading 2

some text

## Heading 3

more text

## Heading 4

### Sub heading

#### Sub Heading
    """
    parser = Parser()
    meta = {"title": ""}
    _, slides = parser.parse_slides(meta, input_data)
    assert len(slides) == 3
    assert meta["title"] == ""
