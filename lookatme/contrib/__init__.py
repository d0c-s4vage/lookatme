"""
This module handles loading and using lookatme_contriba modules

Contrib modules are directly used 
"""


import contextlib


import lookatme.ascii_art
from lookatme.exceptions import IgnoredByContrib
import lookatme.prompt
from . import terminal
from . import file_loader


CONTRIB_MODULES = []


def validate_extension_mod(ext_name, ext_mod):
    """Validate the extension, returns an array of warnings associated with the
    module
    """
    res = []
    if not hasattr(ext_mod, "user_warnings"):
        res.append("'user_warnings' is missing. Extension is not able to "
                   "provide user warnings.")
    else:
        res += ext_mod.user_warnings()

    return res


def load_contribs(contrib_names, safe_contribs, ignore_load_failure=False):
    """Load all contrib modules specified by ``contrib_names``. These should
    all be namespaced packages under the ``lookatmecontrib`` namespace. E.g.
    ``lookatmecontrib.calendar`` would be an extension provided by a
    contrib module, and would be added to an ``extensions`` list in a slide's
    YAML header as ``calendar``.

    ``safe_contribs`` is a set of contrib names that are manually provided
    by the user by the ``-e`` flag or env variable of extensions to auto-load.
    """
    if contrib_names is None:
        return

    errors = []
    all_warnings = []
    for contrib_name in contrib_names:
        module_name = f"lookatme.contrib.{contrib_name}"
        try:
            mod = __import__(module_name, fromlist=[contrib_name])
        except Exception as e:
            if ignore_load_failure:
                continue
            errors.append(str(e))
        else:
            if contrib_name not in safe_contribs:
                ext_warnings = validate_extension_mod(contrib_name, mod)
                if len(ext_warnings) > 0:
                    all_warnings.append((contrib_name, ext_warnings))
            CONTRIB_MODULES.append(mod)

    if len(errors) > 0:
        raise Exception(
            "Error loading one or more extensions:\n\n" + "\n".join(errors),
        )

    if len(all_warnings) == 0:
        return

    print("\nExtension-provided user warnings:")
    for ext_name, ext_warnings in all_warnings:
        print("\n  {!r}:\n".format(ext_name))
        for ext_warning in ext_warnings:
            print("    * {}".format(ext_warning))
    print("")

    if not lookatme.prompt.yes("Continue anyways?"):
        exit(1)


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
