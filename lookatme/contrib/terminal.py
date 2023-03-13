"""
This module defines a built-in contrib module that enables terminal embedding
within a slide.
"""


import re
import shlex
from typing import Dict

import urwid
import yaml
from marshmallow import Schema, fields

import lookatme.config
import lookatme.render
import lookatme.render.markdown_block
from lookatme.exceptions import IgnoredByContrib
from lookatme.render.context import Context


def user_warnings():
    """Provide warnings to the user that loading this extension may cause
    shell commands specified in the markdown to be run.
    """
    return [
        "Code-blocks with a language starting with 'terminal' will cause shell",
        "  commands from the source markdown to be run",
        "See https://lookatme.readthedocs.io/en/latest/builtin_extensions/terminal.html",
        "  for more details",
    ]


class YamlRender:
    @staticmethod
    def loads(data):
        return yaml.safe_load(data)

    @staticmethod
    def dumps(data):
        return yaml.safe_dump(data)


class TerminalExSchema(Schema):
    """The schema used for ``terminal-ex`` code blocks."""

    command = fields.Str()
    rows = fields.Int(dump_default=10, load_default=10)
    init_text = fields.Str(dump_default=None, load_default=None)
    init_wait = fields.Str(dump_default=None, load_default=None)
    init_codeblock = fields.Bool(dump_default=True, load_default=True)
    init_codeblock_lang = fields.Str(dump_default="text", load_default="text")

    class Meta:
        render_module = YamlRender

    def loads(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).loads(*args, **kwargs)
        if res is None:
            raise ValueError("Could not loads")
        if not isinstance(res, dict):
            raise ValueError("Expected a dict")
        return res

    def load(self, *args, **kwargs) -> Dict:
        res = super(self.__class__, self).load(*args, **kwargs)
        if res is None:
            raise ValueError("Could not load")
        if not isinstance(res, dict):
            raise ValueError("Expected a dict")
        return res


CREATED_TERMS = []


def render_fence(token, ctx: Context):
    info = token.get("info", "text")
    lang = info.split()[0]

    numbered_term_match = re.match(r"terminal(\d+)", lang)
    if lang != "terminal-ex" and numbered_term_match is None:
        raise IgnoredByContrib

    if numbered_term_match is not None:
        term_data = TerminalExSchema().load(
            {
                "command": token["content"].strip(),
                "rows": int(numbered_term_match.group(1)),
                "init_codeblock": False,
            }
        )

    else:
        term_data = TerminalExSchema().loads(token["content"])

        if term_data["init_text"] is not None and term_data["init_wait"] is not None:
            init = term_data["init_text"]
            if init.endswith("\n"):
                init = init[:-1]

            term_data["command"] = " ".join(
                [
                    shlex.quote(x)
                    for x in [
                        "expect",
                        "-c",
                        ";".join(
                            [
                                "spawn -noecho {}".format(term_data["command"]),
                                "expect {{{}}}".format(term_data["init_wait"]),
                                "send {{{}}}".format(init),
                                "interact",
                                "exit",
                            ]
                        ),
                    ]
                ]
            )

    term = urwid.Terminal(
        shlex.split(term_data["command"].strip()),
        main_loop=ctx.loop,
        encoding="utf8",
    )
    CREATED_TERMS.append(term)

    line_box = urwid.LineBox(urwid.BoxAdapter(term, height=term_data["rows"]))
    line_box.no_cache = ["render"]

    res = []

    if term_data["init_codeblock"] is True:
        fake_token = {
            "content": term_data["init_text"],
            "info": term_data["init_codeblock_lang"],
        }
        with ctx.use_tokens([fake_token]):
            lookatme.render.markdown_block.render_fence(
                fake_token,
                ctx,
            )

    ctx.widget_add(
        [
            urwid.Divider(),
            line_box,
            urwid.Divider(),
        ],
        wrap=True,
    )

    return res


def shutdown():
    for idx, term in enumerate(CREATED_TERMS):
        lookatme.config.get_log().debug(
            f"Terminating terminal {idx+1}/{len(CREATED_TERMS)}"
        )
        if term.pid is not None:
            term.terminate()
