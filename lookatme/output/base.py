"""
Base module for lookatme output formats
"""


import os
import shutil
from typing import Any, Dict, Optional, Type


import lookatme.config as config
from lookatme.pres import Presentation
import lookatme.templating as templating


THIS_DIR = os.path.realpath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(THIS_DIR, "templates")
DEFINED_TYPES: Dict[str, Type["BaseOutputFormat"]] = {}


class OutputOptionError(ValueError):
    pass


class MissingExtraDependencyError(Exception):
    pass


class BaseOutputFormatMeta(type):
    def __new__(cls, subclass_name, bases, attrs):
        res = super().__new__(cls, subclass_name, bases, attrs)

        res_name = getattr(res, "NAME", None)
        if res_name is not None:
            DEFINED_TYPES[res_name] = res  # type: ignore

        return res


class BaseOutputFormat(metaclass=BaseOutputFormatMeta):
    NAME = None
    DEFAULT_OPTIONS = {}
    REQUIRED_BINARIES = []

    def __init__(self):
        self._curr_options = None
        self.log = config.get_log().getChild(f"Output[{self.NAME}]")

    def format_pres(self, pres: Presentation, output_path: str, options: Dict):
        """Perform the action of outputting the presentation to this specific
        output format.
        """
        for required_bin in self.REQUIRED_BINARIES:
            if not shutil.which(required_bin):
                raise RuntimeError(
                    (
                        f"Could not convert to {self.NAME} format, "
                        f"required binary {required_bin!r} not found"
                    )
                )

        self.log.info(f"Converting presentation to {self.NAME} format")
        self._curr_options = options
        self.do_format_pres(pres, output_path)
        self.log.info(f"  Results in {output_path}")

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        return templating.render(template_path, context)

    def do_format_pres(self, pres: Presentation, output_path: str):
        """Perform the action of outputting the presentation to this specific
        output format.
        """
        raise NotImplementedError("do_format_pres is not implemented")

    def opt(self, option_name: str, category: Optional[str] = None):
        """Fetch the oiption named ``option_name``. If the category isn't
        specified, the current formatter's options are used.

        This function also ensures the defaults are used if the key doesn't
        already exist in the provided options dict.
        """
        opts = self._curr_options or {}
        category = category or self.NAME
        full_option = f"{category}.{option_name}"

        try:
            if full_option not in opts:
                if category in (None, self.NAME):
                    return self.DEFAULT_OPTIONS[option_name]
            return opts[full_option]
        except KeyError:
            raise OutputOptionError(
                f"Option {option_name} ({full_option!r}) does not exist"
            )
