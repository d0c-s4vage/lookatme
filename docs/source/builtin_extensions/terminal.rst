
Terminal Extension
==================

The :any:`lookatme.contrib.terminal` builtin extension allows terminals to be
embedded within slides.

Format
------

The terminal extension modifies the code block markdown rendering by intercepting
code blocks whose language has the format ``terminal\d+``. The number following
the ``terminal`` string indicates how many rows the terminal should use when
rendered (the height).

E.g.

.. code-block:: md

    ```terminal8
    bash -il
    ```

The content of the code block is the command to be run in the terminal. Clicking
inside of the terminal gives the terminal focus, which will allow you to
interact with it, type in it, etc.

To escape from the terminal, press ``ctrl+a``.
