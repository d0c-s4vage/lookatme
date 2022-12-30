[![Master Build Status](https://travis-ci.org/d0c-s4vage/lookatme.svg?branch=master)](https://travis-ci.org/d0c-s4vage/lookatme)
[![Coverage Status](https://coveralls.io/repos/github/d0c-s4vage/lookatme/badge.svg?branch=master)](https://coveralls.io/github/d0c-s4vage/lookatme?branch=master)
[![PyPI Statistics](https://img.shields.io/pypi/dm/lookatme)](https://pypistats.org/packages/lookatme)
[![Latest Release](https://img.shields.io/pypi/v/lookatme)](https://pypi.python.org/pypi/lookatme/)
[![Documentation Status](https://readthedocs.org/projects/lookatme/badge/?version=latest)](https://lookatme.readthedocs.io/en/latest/)

[![Twitter Follow](https://img.shields.io/twitter/follow/d0c_s4vage?style=plastic)](https://twitter.com/d0c_s4vage)

# `lookatme`

`lookatme` is an interactive, extensible, terminal-based markdown presentation
tool.

## TOC

- [TOC](#toc)
- [Features](#features)
  * [Tour](#tour)
- [Navigating the Presentation](#navigating-the-presentation)
- [CLI Options](#cli-options)
- [Known Extensions](#known-extensions)
- [Documentation](#documentation)

## Features

* Markdown rendering
* Built-in tutorial slides `lookatme --tutorial`
* Live (input file modification time watching) and manual reloading
* Live terminals embedded directly in slides
* Syntax highlighting using [Pygments](https://pygments.org/)
* Loading external files into code blocks
* Support for contrib extensions
* Smart slide splitting
* Progressive slides by adding `<!-- stop -->` comments anywhere

### Tutorial

```bash
pip install --upgrade lookatme
lookatme --tutorial
```

General tour

![lookatme_tour](docs/source/_static/lookatme_tour.gif)

Embedded terminal example

![terminal example](docs/source/_static/ext_terminal_example.gif)

Sourcing external files example

![file loader example](docs/source/_static/ext_file_loader_example.gif)

## Navigating the Presentation

| Action                         | Keys                             | Notes |
|--------------------------------|----------------------------------|-------|
| Next Slide                     | `l j right space`                |       |
| Prev Slide                     | `h k left delete backspace`      |       |
| Quit                           | `q Q`                            |       |
| Terminal Focus                 | Click on the terminal            |       |
| Exit Terminal                  | `ctrl+a` and then a slide action |       |
| Vertically scroll within slide | `up/down or page up/page down`   |       |

## CLI Options

```
Usage: lookatme [OPTIONS] [INPUT_FILES]...

  lookatme - An interactive, terminal-based markdown presentation tool.

  See https://lookatme.readthedocs.io/en/v3.0.0rc1 for documentation

Options:
  --debug
  -l, --log PATH
  --tutorial TEXT                 As a flag: show all tutorials. With a
                                  value/comma-separated values: show the
                                  specific tutorials. Use the value 'help' for
                                  more help
  -t, --theme [dark|light]
  --style [default|emacs|friendly|friendly_grayscale|colorful|autumn|murphy|manni|material|monokai|perldoc|pastie|borland|trac|native|fruity|bw|vim|vs|tango|rrt|xcode|igor|paraiso-light|paraiso-dark|lovelace|algol|algol_nu|arduino|rainbow_dash|abap|solarized-dark|solarized-light|sas|staroffice|stata|stata-light|stata-dark|inkpot|zenburn|gruvbox-dark|gruvbox-light|dracula|one-dark|lilypond|nord|nord-darker|github-dark]
  --dump-styles                   Dump the resolved styles that will be used
                                  with the presentation to stdout
  --live, --live-reload           Watch the input filename for modifications
                                  and automatically reload
  -s, --safe                      Do not load any new extensions specified in
                                  the source markdown. Extensions specified
                                  via env var or -e are still loaded
  --no-ext-warn                   Load new extensions specified in the source
                                  markdown without warning
  -i, --ignore-ext-failure        Ignore load failures of extensions
  -e, --exts TEXT                 A comma-separated list of extension names to
                                  automatically load (LOOKATME_EXTS)
  --single, --one                 Render the source as a single slide
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```

## Known Extensions

Below is a list of known extensions for lookatme:

| Extension Name | Install Name                                                                                     | Notes                                                                                                                         |
|----------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| qrcode         | [lookatme.contrib.qrcode](https://github.com/d0c-s4vage/lookatme.contrib.qrcode)                 | Renders QR codes from code blocks                                                                                             |
| image_ueberzug | [lookatme.contrib.image_ueberzug](https://github.com/d0c-s4vage/lookatme.contrib.image_ueberzug) | Renders images with [ueberzug](https://github.com/seebye/ueberzug) (Linux only)                                               |
| render         | [lookatme.contrib.render](https://github.com/d0c-s4vage/lookatme.contrib.render)                 | Renders supported code blocks (graphviz and mermaid-js) by calling an external program. requires an image-rendering extension |

## Documentation

See the [documentation](https://lookatme.readthedocs.io/en/latest/) for details.
