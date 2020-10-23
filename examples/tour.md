---
title: lookatme Tour
date: 2020-10-09
author: James Johnson
extensions:
  - terminal
  - qrcode
  - image_ueberzug
styles:
  style: monokai
  table:
    column_spacing: 15
  margin:
    top: 3
    bottom: 0
  padding:
    top: 3
    bottom: 3
---

# Markdown Support: Inline

|                         Markdown | Result                         |
|---------------------------------:|--------------------------------|
|                       `*italic*` | *italic*                       |
|                       `_italic_` | _italic_                       |
|                       `**bold**` | **bold**                       |
|                       `__bold__` | __bold__                       |
|           `***bold underline***` | ***bold underline***           |
|           `___bold underline___` | ___bold underline___           |
|              `~~strikethrough~~` | ~~strikethrough~~              |
| `[CLICK ME](https://google.com)` | [CLICK ME](https://google.com) |
|                     `` `code` `` | `code`                         |

---

# Markdown Support: Headers

## Heading 2

### Heading 3

#### Heading 4

More text

---

# Markdown Support: Code Blocks & Quotes

Code blocks with language syntax highlighting

~~~python
def a_function(arg1, arg2):
    """This is a function
    """
    print(arg1)
~~~

A quote is below:

> This is a quote more quote contents

---

# Markdown Support: Lists

* Top level
    * Level 2
        * Level 3
            * Level 4
    * Level 2
        * Level 3
            * Level 4
    * Level 2
        * Level 3
            * Level 4

---

# Markdown Support: Numbered Lists

* Top level
    1. Level 2
        1. Level 3
        1. Level 3
        1. Level 3
            * Level 4
    1. Level 2
        1. Level 3
            1. Level 4
            1. Level 4
            1. Level 4
    1. Level 2
        * Level 3
            * Level 4

---

# Extensions

lookatme supports extensions that can add additional functionality to lookatme
presentations.

---

# Extensions > QR Codes

E.g., with the [qrcode](https://github.com/d0c-s4vage/lookatme.contrib.qrcode)
extension enabled, this:

~~~
```qrcode
hello
```
~~~

becomes

```qrcode
hello
```
---

# Extensions > Images

![15](./nasa_orion.jpg)

Extensions can also provide support for images! the
[image_ueberzug](https://github.com/d0c-s4vage/lookatme.contrib.image_ueberzug)
plugin makes images work in slides!

---

# Embeddable Terminals

Terminals can be embedded directly into slides!

The markdown below:

~~~md
```terminal8
bash -il
```
~~~

becomes

```terminal8
bash -il
```

---

# Embeddable Terminals: Docker containers

Want to drop directly into a docker container for a clean environment
in the middle of a slide?

~~~md
```terminal8
docker run --rm -it ubuntu:18.04
```
~~~

```terminal8
docker run --rm -it ubuntu:18.04
```

---

# Live Editing

Hello from vim! The `--live` flag makes lookatme watch the source input
for file changes and auto-reloads the slides.

---

# Live Editing: Including Styles!

```python
def a_function(test):
    print "Hello again from vim again"
```

| h1     | h2     | h3    |
|--------|--------|-------|
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |

--- 

# Slide Scrolling

* Slides
* Can
* Be
* Scrolled
* With
* Up
* And
* Down
* Arrows
* **NOTE**
  - Does
  - Not
  - Work
  - Well
  - With
  - Images
