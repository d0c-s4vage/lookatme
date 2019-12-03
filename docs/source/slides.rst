.. _slides:

Slides
======

Slides in ``lookatme`` are:

  * Separated by hrule elements: ``---`` in Markdown
  * Resized to fit the current window

Metadata
--------

Slide metadata is contained within an optional YAML header:

.. code-block:: md

    ---
    title: TITLE
    author: AUTHOR
    date: 2019-12-02
    extensions: []
    styles: {}
    ---

Extensions
^^^^^^^^^^

Extensions are lookatme contrib modules that redefine lookatme behavior. E.g.,
the ``lookatmecontrib.calendar`` example in the
`examples folder <https://github.com/d0c-s4vage/lookatme/tree/master/examples/calendar_contrib>`_
redefines the ``render_code`` function found in ``lookatme/render/markdown_block.py``.

The original ``render_code`` function gives contrib extensions first-chance at
handling any function calls. Contrib extensions are able to ignore function
calls, and thus allow the default ``lookatme`` behavior, by raising the
:any:`IgnoredByContrib` exception:

.. code-block:: python

    import datetime
    import calendar
    import urwid


    from lookatme.exceptions import IgnoredByContrib


    def render_code(token, body, stack, loop):
        lang = token["lang"] or ""
        if lang != "calendar":
            raise IgnoredByContrib()
        
        today = datetime.datetime.utcnow()
        return urwid.Text(calendar.month(today.year, today.month))
 
Styles
^^^^^^

In addition to the ``--style`` and ``--theme`` CLI options for lookatme, the
slide metadata may explicitly override styling behaviors within lookatme:

.. code-block:: md

    ---
    title: TITLE
    author: AUTHOR
    date: 2019-12-02
    styles:
      style: monokai
      table:
        column_spacing: 3
        header_divider: "-"
    ---

    # Slide 1

    text

The final, resolved styling settings that will be used when displaying a
markdown source is viewable by adding the ``--dump-styles`` flag as a command-line
argument.

See the :ref:`default_style_settings` for a full list of available, overrideable
styles.
