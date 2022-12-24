"""
This module provides basic templating functionality
"""


import json
import os
import re
from typing import Dict


import lookatme.utils.colors as colors


TEMPLATE_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)), "templates")


def get_template_data(template_name: str) -> str:
    """Return the template data or raise an error."""
    template_path = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(template_path) and os.path.isfile(template_path):
        raise ValueError("Template {!r} doesn't exist".format(template_path))

    with open(template_path, "r") as f:
        template_data = f.read()

    return template_data


def render(template_name: str, context: Dict[str, str]) -> str:
    """Render the indicated template name using the provided
    context to resolve variables. An error will be thrown if
    variables are not resolved.
    """
    template_data = get_template_data(template_name)

    filters = "|".join(get_filters().keys())

    regex = r"\{\{([a-zA-Z0-9_\.]+)(?:\|(" + filters + r"))?\}\}"
    vars_to_replace = set(re.findall(regex, template_data))
    undefined_vars = set(r[0] for r in vars_to_replace) - set(context.keys())
    if undefined_vars:
        raise ValueError("Undefined template variables: {!r}".format(undefined_vars))

    filters = {
        "json": json_filter,
        "css": css_filter,
        "highlight": highlight_filter,
    }

    for var, var_filter in vars_to_replace:
        replace_val = context[var]

        if var_filter == "":
            replace_text = var
            replace_val = str(replace_val)

        else:
            filter_fn = filters.get(var_filter)
            if filter_fn is None:
                raise ValueError("Unsupported filter: {!r}".format(var_filter))
            replace_text = var + "|" + var_filter
            replace_val = filter_fn(replace_val)

        template_data = template_data.replace("{{" + replace_text + "}}", replace_val)

    return template_data


_FILTERS = {}


def get_filters() -> Dict:
    global _FILTERS
    if not _FILTERS:
        _FILTERS = {
            "json": json_filter,
            "css": css_filter,
            "highlight": highlight_filter,
        }

    return _FILTERS


def json_filter(value) -> str:
    return json.dumps(value)


def css_filter(value: str) -> str:
    styles = {}
    parts = [x.strip() for x in value.split(",")]
    for part in parts:
        if part.startswith("#"):
            styles["color"] = part
        elif part == "underline":
            styles["text-decoration"] = comma_append(
                styles.get("text-decoration", ""), "underline"
            )
        elif part == "italic":
            styles["font-style"] = "italic"
        elif part == "strikethrough":
            styles["text-decoration"] = comma_append(
                styles.get("text-decoration", ""), "line-through"
            )
        elif part == "bold":
            styles["font-weight"] = "bold"

    res = []
    for style, style_val in styles.items():
        res.append(f"{style}: {style_val};")

    return " ".join(res)


def highlight_filter(value: str) -> str:
    return colors.get_highlight_color(value, 0.2)


def comma_append(val, new_val):
    if val:
        return new_val
    else:
        return val + "," + new_val
