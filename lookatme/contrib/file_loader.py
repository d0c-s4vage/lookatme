"""
This module defines a built-in contrib module that enables external files to
be included within the slide. This is extremely useful when having source
code displayed in a code block, and then running/doing something with the
source data in a terminal on the same slide.
"""


from marshmallow import fields, Schema
import os
import subprocess
import yaml


import lookatme.config
from lookatme.exceptions import IgnoredByContrib


class YamlRender:
    loads = lambda data: yaml.safe_load(data)
    dumps = lambda data: yaml.safe_dump(data)


class LineRange(Schema):
    start = fields.Integer(default=0, missing=0)
    end = fields.Integer(default=None, missing=None)


class FileSchema(Schema):
    path = fields.Str()
    relative = fields.Boolean(default=True, missing=True)
    lang = fields.Str(default="auto", missing="auto")
    transform = fields.Str(default=None, missing=None)
    lines = fields.Nested(
        LineRange,
        default=LineRange().dump(LineRange()),
        missing=LineRange().dump(LineRange()),
    )

    class Meta:
        render_module = YamlRender


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


def render_code(token, body, stack, loop):
    """Render the code, ignoring all code blocks except ones with the language
    set to ``file``.
    """
    lang = token["lang"] or ""
    if lang != "file":
        raise IgnoredByContrib

    file_info_data = token["text"]
    file_info = FileSchema().loads(file_info_data)

    # relative to the slide source
    if file_info["relative"]:
        base_dir = lookatme.config.SLIDE_SOURCE_DIR
    else:
        base_dir = os.getcwd()

    full_path = os.path.join(base_dir, file_info["path"])
    if not os.path.exists(full_path):
        token["text"] = "File not found"
        token["lang"] = "text"
        raise IgnoredByContrib
    
    with open(full_path, "rb") as f:
        file_data = f.read()

    if file_info["transform"] is not None:
        file_data = transform_data(file_info["transform"], file_data)

    lines = file_data.split(b"\n")
    lines = lines[file_info["lines"]["start"]:file_info["lines"]["end"]]
    file_data = b"\n".join(lines)
    token["text"] = file_data
    token["lang"] = file_info["lang"]
    raise IgnoredByContrib
