.. _style_precedence:

Style Precedence
================

Styling may be set in three locations in lookatme:

  1. In a theme
  2. In a slide's YAML header
  3. On the command-line

When constructing the final, resolved style set that will be used to render
markdown, lookatme starts with the default style settings defined in
:any:`lookatme.schemas`, and then applies overrides in the order specified
above.

Overrides are applied by performing a deep merge of nested dictionaries. For
example, if the default styles defined in schemas.py were:

.. code-block:: yaml

    headings:
      "1":
        fg: "#33c,bold"
        bg: "default"
      "2":
        fg: "#222,bold"
        bg: "default"

... and if the style overrides defined by a theme were:

.. code-block:: yaml

    headings:
      "1":
        bg: "#f00"

... and if the style overrides defined in the slide YAML header were:


.. code-block:: yaml

    headings:
      "2":
        fg: "#f00,bold,underline"

The final, resolved style settings for rendering the markdown would be:

.. code-block:: yaml

    headings:
      "1":
        fg: "#33c,bold"
        bg: "#f00" # from the theme
      "2":
        fg: "#f00,bold,underline" # from the slide YAML header
        bg: "default"


.. _default_style_settings:

Default Style Settings
----------------------

The default styles and formats are defined in the marshmallow schemas in
:any:`lookatme.schemas`. The dark theme is an empty theme with no overrides
(the defaults *are* the dark theme):

.. code-block:: yaml


    title:
      bg: default
      fg: '#f30,bold,italics'
    author:
      bg: default
      fg: '#f30'
    date:
      bg: default
      fg: '#777'
    slides:
      bg: default
      fg: '#f30'
    bullets:
      '1': •
      '2': ⁃
      '3': ◦
      default: •
    headings:
      '1':
        bg: default
        fg: '#9fc,bold'
        prefix: '██ '
        suffix: ''
      '2':
        bg: default
        fg: '#1cc,bold'
        prefix: '▓▓▓ '
        suffix: ''
      '3':
        bg: default
        fg: '#29c,bold'
        prefix: '▒▒▒▒ '
        suffix: ''
      '4':
        bg: default
        fg: '#559,bold'
        prefix: '░░░░░ '
        suffix: ''
      default:
        bg: default
        fg: '#346,bold'
        prefix: '░░░░░ '
        suffix: ''
    link:
      bg: default
      fg: '#33c,underline'
    quote:
      bottom_corner: └
      side: ╎
      style:
        bg: default
        fg: italics,#aaa
      top_corner: ┌
    style: monokai
    table:
      column_spacing: 3
      header_divider: ─
