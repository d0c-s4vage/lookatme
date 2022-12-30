# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import locale
import os
import sys


def fake_locale_set(*args, **kwargs):
    try:
        locale.setlocale(*args, **kwargs)
    except Exception:
        pass
orig_set_locale = locale.setlocale
locale.setlocale = fake_locale_set
import urwid
locale.setlocale = orig_set_locale


PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_SOURCE_DIR = os.path.abspath(os.path.dirname(__file__))


def read_file(*parts):
    with open(os.path.join(PROJECT_DIR, *parts), "r") as f:
        return f.read()


# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'lookatme'
copyright = "2019, James 'd0c-s4vage' Johnson"
author = "James 'd0c-s4vage' Johnson"


# The full version, including alpha/beta/rc tags
release = os.environ.get("READTHEDOCS_VERSION", '3.0.0rc1')


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

master_doc = "index"

#-----------------------------------------------------------------------------
# Generate list of overrideable funcitons within lookatme
#-----------------------------------------------------------------------------


def get_contrib_functions(*file_parts):
    render_module = file_parts[-1].replace(".py", "")
    full_mod_path = ".".join(list(file_parts[:-1]) + [render_module])
    lines = read_file(*file_parts).split("\n")

    res = []
    in_contrib = False
    for idx, line in enumerate(lines):
        line = line.strip()

        if "@contrib_first" == line:
            in_contrib = True
            continue
        if line.startswith("@"):
            continue
        elif line.startswith("def "):
            if in_contrib:
                fn_name = line.split()[1].split("(")[0]
                res.append(f":any:`{fn_name} <{full_mod_path}.{fn_name}>`")
            in_contrib = False
    return res


contrib_fns = []
contrib_fns += get_contrib_functions("lookatme", "render", "markdown_block.py")
contrib_fns += get_contrib_functions("lookatme", "render", "markdown_inline.py")
contrib_fns += get_contrib_functions("lookatme", "tui.py")


list_text = []
for fn_ref in contrib_fns:
    list_text.append(f"  * {fn_ref}")
list_text = "\n".join(list_text)


with open(os.path.join(DOCS_SOURCE_DIR, "contrib_extensions.rst"), "r") as f:
    orig_data = f.read()

new_data = orig_data.replace("LOOKATME_OVERRIDES", list_text)

with open(os.path.join(DOCS_SOURCE_DIR, "contrib_extensions_auto.rst"), "w") as f:
    f.write(new_data)


def run_apidoc(_):
	from sphinx.ext.apidoc import main
	import os
	import sys

	sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
	cur_dir = os.path.abspath(os.path.dirname(__file__))
	module = os.path.join(cur_dir, "..", "..", "lookatme")
	main(["-e", "-o", os.path.join(cur_dir, "autodoc"), module, "--force"])


def setup(app):
	app.connect('builder-inited', run_apidoc)
