---
title: lookatme Tour
date: 2019-12-02
author: James Johnson
styles:
  table:
    column_spacing: 5
---

# Live Editing

lookatme supports live editing with the `--live` command-line argument.

---

# Live Editing: Including Styles!

```python
def a_function(test):
    pass
```

| h1     | h2     | h3    |
|--------|--------|-------|
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |
| value1 | value2 | value3 |

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

> This is a quote

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

# Embeddable Terminals: Asciinema Replays

Asciinema is an awesome tool for recording and sharing terminal commands.
If you have asciinema installed (`pip install asciinema`), play back a
pre-recorded shell session inside of a slide!

```terminal13
asciinema play https://asciinema.org/a/ivEsIJrcC8bT73Yx9qdPRfYsc
```
