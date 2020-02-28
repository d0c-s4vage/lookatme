
Terminal Extension
==================

The :any:`lookatme.contrib.terminal` builtin extension allows terminals to be
embedded within slides.

Basic Format
------------

The terminal extension modifies the code block markdown rendering by intercepting
code blocks whose language has the format ``terminal\d+``. The number following
the ``terminal`` string indicates how many rows the terminal should use when
rendered (the height).

Usage
*****

E.g.

.. code-block:: md

    ```terminal8
    bash -il
    ```

The content of the code block is the command to be run in the terminal. Clicking
inside of the terminal gives the terminal focus, which will allow you to
interact with it, type in it, etc.

To escape from the terminal, press ``ctrl+a``.

Extended Format
---------------

The terminal extension also has a `terminal-ex` mode that can be used as the
language in a code block. When `terminal-ex` is used, the contents of the code
block must be YAML that conforms to the :any:`TerminalExSchema` schema.

The default schema is shown below:

.. code-block:: yaml

   command: "the command to run"  # required
   rows: 10                       # number of rows for the terminal (height)
   init_text: null                # initial text to feed to the command. This is
                                  #     useful to, e.g., pre-load text on a
                                  #     bash prompt so that only "enter" must be
                                  #     pressed. Uses the `expect` command.
   init_wait: null                # the prompt (string) to wait for with `expect`
                                  #     this is required if init_text is set.
   init_codeblock: true           # show a codeblock with the init_text as its
                                  # content
   init_codeblock_lang: text      # the language of the init codeblock

Usage
*****

E.g.

.. code-block:: md

   ```terminal-ex
   command: bash -il
   rows: 20
   init_text: echo hello
   init_wait: '$> '
   init_codeblock_lang: bash
   ```
