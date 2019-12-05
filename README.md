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

- [TOC](#toc)
- [Features](#features)
  * [Tour](#tour)
- [Navigating the Presentation](#navigating-the-presentation)
- [CLI Options](#cli-options)
- [Documentation](#documentation)

## Features

* Markdown rendering
* Live (input file modification time watching) and manual reloading
* Live terminals embedded directly in slides
* Syntax highlighting using [Pygments](https://pygments.org/)
* Support for contrib extensions

### Tour

![lookatme_tour](docs/source/_static/lookatme_tour.gif)

## Navigating the Presentation

| Action         | Keys                             | Notes |
|----------------|----------------------------------|-------|
| Next Slide     | `l j down right space`           |       |
| Prev Slide     | `h k up left delete backspace`   |       |
| Quit           | `q Q`                            |       |
| Terminal Focus | Click on the terminal            |       |
| Exit Terminal  | `ctrl+a` and then a slide action |       |

## CLI Options

```
Usage: lookatme [OPTIONS] [INPUT_FILE]

  lookatme - An interactive, terminal-based markdown presentation tool.

Options:
  --debug
  -l, --log PATH
  -t, --theme [dark|light]
  -s, --style [default|emacs|friendly|colorful|autumn|murphy|manni|monokai|perldoc|pastie|borland|trac|native|fruity|bw|vim|vs|tango|rrt|xcode|igor|paraiso-light|paraiso-dark|lovelace|algol|algol_nu|arduino|rainbow_dash|abap|solarized-dark|solarized-light|sas|stata|stata-light|stata-dark]
  --dump-styles                   Dump the resolved styles that will be used
                                  with the presentation to stdout
  --live, --live-reload           Watch the input filename for modifications
                                  and automatically reload
  --help                          Show this message and exit.
```

## Documentation

See the [documentation](https://lookatme.readthedocs.io/en/latest/) for details.
