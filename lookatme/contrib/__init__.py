"""
This module handles loading and using lookatme_contriba modules

Contrib modules are directly used 
"""


import contextlib


from lookatme.exceptions import IgnoredByContrib
from . import terminal
from . import file_loader


CONTRIB_MODULES = [
    terminal,
    file_loader,
]


def load_contribs(contrib_names):
    """Load all contrib modules specified by ``contrib_names``. These should
    all be namespaced packages under the ``lookatmecontrib`` namespace. E.g.
    ``lookatmecontrib.calendar`` would be an extension provided by a
    contrib module, and would be added to an ``extensions`` list in a slide's
    YAML header as ``calendar``.
    """
    if contrib_names is None:
        return

    errors = []
    for contrib_name in contrib_names:
        module_name = f"lookatme.contrib.{contrib_name}"
        try:
            mod = __import__(module_name, fromlist=[contrib_name])
            CONTRIB_MODULES.append(mod)
        except Exception as e:
            errors.append(str(e))

    if len(errors) > 0:
        raise Exception(
            "Error loading one or more extensions:\n\n" + "\n".join(errors),
        )


def contrib_first(fn):
    """A decorator that allows contrib modules to override default behavior
    of lookatme. E.g., a contrib module may override how a table is displayed
    to enable sorting, or enable displaying images rendered with ANSII color
    codes and box drawing characters, etc.

    Contrib modules may ignore chances to override default behavior by raising
    the ``lookatme.contrib.IgnoredByContrib`` exception.
    """
    fn_name = fn.__name__

    @contextlib.wraps(fn)
    def inner(*args, **kwargs):
        for mod in CONTRIB_MODULES:
            if not hasattr(mod, fn_name):
                continue
            try:
                return getattr(mod, fn_name)(*args, **kwargs)
            except IgnoredByContrib:
                pass

        return fn(*args, **kwargs)

    return inner


def shutdown_contribs():
    """Call the shutdown function on all contrib modules
    """
    for mod in CONTRIB_MODULES:
        getattr(mod, "shutdown", lambda: 1)()
