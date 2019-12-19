
File Loader Extension
=====================

The :any:`lookatme.contrib.file_loader` builtin extension allows external
files to be sourced into the code block, optionally being transformed and
optionally restricting the range of lines to display.

Format
------

The file loader extension modifies the code block markdown rendering by intercepting
code blocks whose language equals ``file``. The contents of the code block must
be YAML that conforms to the :any:`FileSchema` schema.

The default schema is shown below:

.. code-block:: yaml

    path: path/to/the/file # required
    relative: true         # relative to the slide source directory
    lang: text             # pygments language to render in the code block
    transform: null        # optional shell command to transform the file data
    lines:
      start: 0
      end: null

.. note::

    The line range is only applied **AFTER** transformations are performed on
    the file data.

Usage
-----

E.g.

.. code-block:: md

    ```file
    path: ../source/main.c
    lang: c
    ```
