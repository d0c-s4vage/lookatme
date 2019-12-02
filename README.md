[![Master Build Status](https://travis-ci.org/d0c-s4vage/lookatme.svg?branch=master)](https://travis-ci.org/d0c-s4vage/lookatme)
[![Coverage Status](https://coveralls.io/repos/github/d0c-s4vage/lookatme/badge.svg?branch=master)](https://coveralls.io/github/d0c-s4vage/lookatme?branch=master)
[![PyPI Statistics](https://img.shields.io/pypi/dm/lookatme)](https://pypistats.org/packages/lookatme)
[![Latest Release](https://img.shields.io/pypi/v/lookatme)](https://pypi.python.org/pypi/lookatme/)
[![Documentation Status](https://readthedocs.org/projects/lookatme/badge/?version=latest)](https://lookatme.readthedocs.io/en/latest/)

# `lookatme`

`lookatme` is an interactive, extensible, terminal-based markdown presentation
tool.

**NOTE** `lookatme` is still under heavy development. Use at your own risk until
version `1.0.0` is released!

## TOC

- [Features](#features)
  * [Live Reloading](#live-reloading)
- [Navigating the Presentation](#navigating-the-presentation)
- [CLI Options](#cli-options)
- [Slide Format](#slide-format)
  * [Metadata Header](#metadata-header)
  * [Slides](#slides)

## Features

* Markdown rendering
* Live (input file modification time watching) and manual reloading
* Live terminals embedded directly in slides
* Syntax highlighting using [Pygments](https://pygments.org/)

### Live Reloading

![lookatme_live_editing](https://user-images.githubusercontent.com/5090146/69895932-b74c4700-12ed-11ea-9fca-bba68d323502.gif)

## Navigating the Presentation

| Action         | Keys                             | Notes |
|----------------|----------------------------------|-------|
| Next Slide     | `l j down right space`           |       |
| Prev Slide     | `h k up left delete backspace`   |       |
| Quit           | `q Q`                            |       |
| Terminal Focus | Click on the terminal            |       |
| Exit Terminal  | `ctrl+a` and then a slide action |       |

## CLI Options

## Slide Format

### Metadata Header

The metadata header has the following fields:

```yaml
title: TITLE
author: AUTHOR
date: DATE
extensions: []
styles: {}
```

For all supported styles overrides, please see the `--dump-styles` CLI argument

### Slides
