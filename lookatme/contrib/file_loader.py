"""
This module defines a built-in contrib module that enables external files to
be included within the slide. This is extremely useful when having source
code displayed in a code block, and then running/doing something with the
source data in a terminal on the same slide.
"""


import os
import subprocess
from typing import Dict

import yaml
from marshmallow import Schema, fields

import lookatme.config
from lookatme.exceptions import IgnoredByContrib
from lookatme.render.context import Context


def user_warnings():
    """Provide warnings to the user that loading this extension may cause
    shell commands specified in the markdown to be run.
    """
    return [
        "Code-blocks with a language starting with 'file' may cause shell",
        "  commands from the source markdown to be run if the 'transform'",
        "  field is set",
        "See https://lookatme.readthedocs.io/en/latest/builtin_extensions/file_loader.html",
        "  for more details",
    ]


class YamlRender:
    @staticmethod
    def loads(data):
        return yaml.safe_load(data)

    @staticmethod
    def dumps(data):
        return yaml.safe_dump(data)


class LineRange(Schema):
    start = fields.Integer(dump_default=0, load_default=0)
    end = fields.Integer(dump_default=None, load_default=None)


class FileSchema(Schema):
    path = fields.Str()
    relative = fields.Boolean(dump_default=True, load_default=True)
    lang = fields.Str(dump_default="auto", load_default="auto")
    transform = fields.Str(dump_default=None, load_default=None)
    lines = fields.Nested(
        LineRange,
        dump_default=LineRange().dump(None),
        load_default=LineRange().dump(None),
    )

    class Meta:
        render_module = YamlRender

    def loads(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).loads(*args, **kwargs)
        if res is None:
            raise ValueError("Could not loads")
        return res

    def load(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).load(*args, **kwargs)
        if res is None:
            raise ValueError("Could not load")
        return res


def transform_data(transform_shell_cmd, input_data):
    """Transform the ``input_data`` using the ``transform_shell_cmd``
    shell command.
    """
    proc = subprocess.Popen(
        transform_shell_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
    )
    stdout, _ = proc.communicate(input=input_data)
    return stdout


def render_fence(token: Dict, ctx: Context):
    """Render the code, ignoring all code blocks except ones with the language
    set to ``file``.
    """
    info = token.get("info", None) or "text"
    lang = info.split()[0]
    if lang != "file":
        raise IgnoredByContrib

    file_info_data = token["content"]
    file_info = FileSchema().loads(file_info_data)

    # relative to the slide source
    if file_info["relative"]:
        base_dir = lookatme.config.SLIDE_SOURCE_DIR
    else:
        base_dir = os.getcwd()

    full_path = os.path.join(base_dir, file_info["path"])
    if not os.path.exists(full_path):
        token["content"] = "File not found"
        token["info"] = "text"
        raise IgnoredByContrib

    with open(full_path, "rb") as f:
        file_data = f.read()

    if file_info["transform"] is not None:
        file_data = transform_data(file_info["transform"], file_data)

    lines = file_data.split(b"\n")
    lines = lines[file_info["lines"]["start"] : file_info["lines"]["end"]]
    file_data = b"\n".join(lines)
    token["content"] = file_data
    token["info"] = file_info["lang"]
    raise IgnoredByContrib
