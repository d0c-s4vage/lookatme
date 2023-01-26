[![PyPI Statistics](https://img.shields.io/pypi/dm/lookatme)](https://pypistats.org/packages/lookatme)
[![Latest Release](https://img.shields.io/pypi/v/lookatme)](https://pypi.python.org/pypi/lookatme/)
[![Twitter Follow](https://img.shields.io/twitter/follow/d0c_s4vage?style=plastic)](https://twitter.com/d0c_s4vage)

# `lookatme`

`lookatme` is an interactive, extensible, terminal-based markdown presentation
tool.

## Features

* Markdown rendering with inline HTML support
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

![lookatme tutorial gif](https://github.com/d0c-s4vage/lookatme/releases/latest/download/tutorial.gif)

### Documentation

See https://d0c-s4vage.github.io/lookatme for the full documentation

## Known Extensions

Below is a list of known extensions for lookatme:

| Extension Name | Install Name                                                                                     | Notes                                                                                                                         |
|----------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| qrcode         | [lookatme.contrib.qrcode](https://github.com/d0c-s4vage/lookatme.contrib.qrcode)                 | Renders QR codes from code blocks                                                                                             |
| image_ueberzug | [lookatme.contrib.image_ueberzug](https://github.com/d0c-s4vage/lookatme.contrib.image_ueberzug) | Renders images with [ueberzug](https://github.com/seebye/ueberzug) (Linux only)                                               |
| render         | [lookatme.contrib.render](https://github.com/d0c-s4vage/lookatme.contrib.render)                 | Renders supported code blocks (graphviz and mermaid-js) by calling an external program. requires an image-rendering extension |
