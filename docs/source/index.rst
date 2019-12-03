.. lookatme documentation master file, created by
   sphinx-quickstart on Mon Dec  2 06:35:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lookatme
========

``lookatme`` is an interactive, terminal-based markdown presentation tool that
supports:

  * Themes
  * Syntax highlighting
  * Styling and settings embedded within the Markdown YAML header
  * Embedded terminals as part of a presentation
  * Live and manual source reloading
  * User-contrib behavior overrides and extensions

Tour
----

.. image:: _static/lookatme_tour.gif
  :width: 800
  :alt: Tour Gif

TL;DR Getting Started
---------------------

Install ``lookatme`` with:

.. code-block:: bash

    pip install lookatme

Run lookatme on slides written in Markdown:

.. code-block:: bash

    lookatme slides.md

Slides are separated with ``---`` hrules:

.. code-block:: md

    # Slide 1

    Some text

    ---

    # Slide 2

    More text

A basic, optional YAML header may be included at the top of the slides:

.. code-block:: md

    ---
    title: Slides Presentation
    author: Me Not You
    date: 2019-12-02
    ---

    # Slide 1

    Some text

.. toctree::
  :maxdepth: 2

  getting_started
  slides
  dark_theme
  light_theme
  style_precendence


.. toctree::

  autodoc/modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
