# Sample Calendar Contrib

This is a sample lookatmecontrib module that overrides code blocks when the
language is `calendar` to display a text calendar of the current month.

## Example Usage

With this directory on your `PYTHONPATH`, list `calendar` as an extension in
your slide deck's YAML header:

~~~markdown
---
title: An Awesome Presentation
author: James Johnson
date: 2019-11-19
extensions:
  - calendar
styles:
  style: monokai
  table:
    column_spacing: 10
---
~~~

With the extension available and declared, you can now use `calendar` code
blocks to display a calendar of the current month on a slide:

~~~markdown
```calendar

```
~~~

Full command-line, assuming it is run from the root of the lookatme project:

```
PYTHONPATH="./examples/calendar_contrib:$PYTHONPATH" python -m lookatme examples/calendar_contrib/example.md
```

## Future Options

If one desired to build more on top of this toy calendar extension, additional
options could be entered as yaml within the code block:

```calendar
from: 2019-05-01
to: 2019-11-01
```

**NOTE** These are not implemented in this toy extension example.
