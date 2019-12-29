
.. _contrib-extensions:

Contrib Extensions
==================

lookatme allows an extension to override and redefine how markdown is rendered.
Extensions have first-chance opportunities to handle rendering function calls.
Extensions also have the ability to ignore specific rendering function calls
and allow original lookatme behavior (or other extensions) to handle the
call to that rendering function.

For example, an extension may provide its own implementation of the render
function ``render_table`` to provide custom table rendering, such as sortable
rows, alternating row background colors, etc.

Using Extensions
----------------

Extensions are namespace packages within ``lookatme.contrib``. The are used by

  1. Installing the extension with ``pip install lookatme.contrib.XXX``
  2. Adding the extension to the list of extensions required by your slides:

.. code-block:: md

    ---
    title: TITLE
    author: AUTHOR
    date: 2019-11-01
    extensions:
      - XXX
    ---

    # Slide 1

    ...

Extension Layout
----------------

It is highly recommended that you use the `lookatme.contrib-template <https://github.com/d0c-s4vage/lookatme.contrib-template>`_
to create new extensions.

Extensions *must* be a namespaced module within the ``lookatme.contrib``
submodule. The basic tree layout for such an extension is below:

.. code-block:: text

    examples/calendar_contrib/
    ├── lookatme
    │   └── contrib
    │       └── calendar.py
    └── setup.py

Notice that there is not an ``__init__.py`` file in the contrib path. This is
using the `implicit namespace package <https://packaging.python.org/guides/packaging-namespace-packages/#native-namespace-packages>`_
format for creating namespace packages, where an ``__init__.py`` is not
needed.

Extension setup.py
------------------

Below is the ``setup.py`` from the ``examples/calendar_contrib`` extension:

.. literalinclude:: ../../examples/calendar_contrib/setup.py
    :language: python

Overriding Behavior
-------------------

Any function within lookatme that is decorated with ``@contrib_first`` may be
overridden by an extension by defining a function of the same name within the
extension module.

For example, to override the ``render_code`` function that is declared in
lookatme in `lookatme/render/markdown_block.py <https://github.com/d0c-s4vage/lookatme/blob/master/lookatme/render/markdown_block.py>`_,
the example calender extension must declare its own function named
``render_code`` that accepts the same arguments and provides the same return
values as the original function:

.. literalinclude:: ../../examples/calendar_contrib/lookatme/contrib/calendar.py
    :language: python

Notice how the extension code above raises the :any:`IgnoredByContrib` exception
to allow the default lookatme behavior to occur.

Overrideable Functions
----------------------

Below is an automatically generated list of all overrideable functions that
are present in this release of lookatme. See the
:any:`lookatme.tui.SlideRenderer.do_render` function for details on markdown_block
render function arguments and return values.

LOOKATME_OVERRIDES
