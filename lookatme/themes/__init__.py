"""
Defines the built-in styles for lookatme
"""


from lookatme.schemas import StyleSchema
from lookatme.utils import dict_deep_update

from . import dark, light


def ensure_defaults(mod):
    """Ensure that all required attributes exist within the provided module
    """
    defaults = StyleSchema().dump(None)
    dict_deep_update(defaults, mod.theme)
    return defaults
