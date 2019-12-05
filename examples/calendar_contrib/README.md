# Sample Calendar Contrib

This is a sample lookatme.contrib module that overrides code blocks when the
language is `calendar` to display a text calendar of the current month.

## Example Usage

Install this python package into your virtual environment:

```
pip install ./examples/calendar_contrib
```

List the `calendar` extension in the `extensions` section of your slide deck's
YAML header:

~~~markdown
---
title: An Awesome Presentation
author: James Johnson
date: 2019-11-19
extensions:
  - calendar
---
~~~

With the extension available and declared, you can now use `calendar` code
blocks to display a calendar of the current month on a slide:

~~~markdown
```calendar

```
~~~

## Future Options

If one desired to build more on top of this toy calendar extension, additional
options could be entered as yaml within the code block:

```calendar
from: 2019-05-01
to: 2019-11-01
```

**NOTE** These are not implemented in this toy extension example.
