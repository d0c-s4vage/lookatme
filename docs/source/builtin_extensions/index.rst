
Builtin Extensions
==================

``lookatme`` comes with a few built-in extensions.

Builtin Extension Qualification
-------------------------------

Builtin extensions must:

  * Not require extra dependencies just for the extension
  * Be generally useful in most cases

E.g., the qrcode extension has an extra dependency. This immediately
disqualifies it from being a builtin extension.

Usage
-----

Although builtin extensions are defined in the same way as external
:ref:`contrib-extensions`, builtin extensions do not need to be explicitly
declared in the YAML header.

List of Builtin Extensions
--------------------------

.. toctree::
    :maxdepth: 2

    terminal
    file_loader
