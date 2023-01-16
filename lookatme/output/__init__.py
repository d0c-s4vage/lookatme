"""
lookatme output formats
"""


import inspect
from typing import Any, Dict, List, Type


from lookatme.output.base import BaseOutputFormat
import lookatme.config as config
from lookatme.pres import Presentation
from lookatme.tutorial import tutor
from lookatme.output.base import MissingExtraDependencyError


output_modules = ["html", "html_raw", "gif"]
not_installed = []
for output_module in output_modules:
    try:
        __import__(f"lookatme.output.{output_module}", locals(), globals())
    except MissingExtraDependencyError as e:
        not_installed.append(output_module)
        pass


def get_available_to_install_msg() -> str:
    if not not_installed:
        return ""

    return " Install lookatme extras for additional output formats: {}".format(
        ", ".join(f"lookatme[{format}]" for format in not_installed)
    )


def _fmt_val(val: Any) -> str:
    if isinstance(val, str):
        val_str = repr(val)
    elif isinstance(val, list):
        val_str = ",".join(_fmt_val(x) for x in val)
    else:
        val_str = str(val)

    return val_str


def get_output_options_help() -> str:
    from lookatme.output.base import DEFINED_TYPES

    res = []
    res.append("Available options for output formats:\n")

    for format_name, format_cls in DEFINED_TYPES.items():
        for option_name, option_val in format_cls.DEFAULT_OPTIONS.items():
            option_val_str = _fmt_val(option_val)
            res.append(f"    {format_name}.{option_name} = {option_val_str}")
        res.append("")

    return "\n".join(res)


def _get_default_val(option_key) -> Any:
    from lookatme.output.base import DEFINED_TYPES

    if "." not in option_key:
        raise ValueError("Key must have the form <format_name>.<option_name>")

    format_name, option_name = option_key.split(".", 1)
    format_cls = DEFINED_TYPES.get(format_name, None)
    if format_cls is None:
        raise ValueError(
            "Key {!r} must be one of the valid output names:  {}".format(
                format_name, ", ".join(DEFINED_TYPES.keys())
            )
        )

    if option_name not in format_cls.DEFAULT_OPTIONS:
        raise ValueError(
            "Format {!r} option {!r} must be one of the valid format options: {}".format(
                format_name, option_name, ", ".join(format_cls.DEFAULT_OPTIONS.keys())
            )
        )

    return format_cls.DEFAULT_OPTIONS[option_name]


def _convert_to_matching_type(to_convert: Any, base_type: Any):
    if isinstance(base_type, bool):
        to_convert = str(to_convert).lower()
        if to_convert == "true":
            return True
        elif to_convert == "false":
            return False
        else:
            raise ValueError(
                f"Option value {to_convert!r} could not be converted to a bool"
            )
    elif isinstance(base_type, int):
        return int(to_convert)
    elif isinstance(base_type, str):
        return str(to_convert)
    elif isinstance(base_type, float):
        return float(to_convert)
    elif isinstance(base_type, list):
        if not isinstance(to_convert, str):
            raise ValueError("List option types should be strings")
        return [x.strip() for x in to_convert.split(",")]
    else:
        raise RuntimeError(
            "Base output option type {!r} is not supported yet".format(
                type(base_type),
            )
        )


def get_format(format_name: str) -> Type["BaseOutputFormat"]:
    from lookatme.output.base import DEFINED_TYPES

    return DEFINED_TYPES[format_name]


def get_all_formats() -> List[str]:
    from lookatme.output.base import DEFINED_TYPES

    return list(sorted(DEFINED_TYPES.keys()))


def get_all_options() -> List[str]:
    from lookatme.output.base import DEFINED_TYPES

    res = []
    for output_type, output_cls in DEFINED_TYPES.items():
        for option in output_cls.DEFAULT_OPTIONS.keys():
            res.append(f"{output_type}.{option}")
    return res


def parse_options(option_strings: List[str]) -> Dict[str, Any]:
    res = {}

    for option in option_strings:
        parts = option.split("=", 1)
        key = parts[0]
        val = True
        if len(parts) > 1:
            val = parts[1]

        try:
            default_val = _get_default_val(key)
        except ValueError as e:
            config.get_log().warn("Output format option error: {}".format(e))
            continue

        val = _convert_to_matching_type(val, default_val)
        res[key] = val

    return res


@tutor(
    "output",
    "Output Formats",
    inspect.cleandoc(
        r"""
        Lookatme supports saving markdown slides into other output formats with the
        CLI options:

        * `--format` - the format to output the slides in
        * `--output` - the path to output to
        * `--opt FORMAT.OPT_NAME=OPT_VAL` - set options for output formats

        For example, the tutorial slides can be rendered with a width of 80
        columns into an HTML format with the command below:

        ```
        lookatme --tutorial --output /tmp/html --format html --opt html.cols=80
        ```

        Current supported output formats are: {formats}

        All available output options can be viewed with the command below:

        <TUTOR:CLI>lookatme --opt help</TUTOR:CLI>
        """
    ).format(
        formats=", ".join(get_all_formats()),
        options="\n".join(get_output_options_help()),
    ),
)
def output_pres(pres: Presentation, path: str, format: str, options: Dict[str, Any]):
    formatter = get_format(format)()
    formatter.format_pres(pres, path, options)
