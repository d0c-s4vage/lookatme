"""
Defines the built-in styles for lookatme
"""


from typing import Any, Dict

from lookatme.schemas import StyleSchema
from lookatme.utils import dict_deep_update


def ensure_defaults(mod) -> Dict[str, Any]:
    """Ensure that all required attributes exist within the provided module"""
    defaults = StyleSchema().dump(None)
    dict_deep_update(defaults, mod.theme)

    if not isinstance(defaults, dict):
        raise ValueError("Schemas didn't return a dict")

    return defaults
