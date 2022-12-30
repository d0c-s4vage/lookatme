# Changelog

- [v2.5.1](#v255)
- [v2.5.0](#v250)
- [v2.4.1](#v241)
- [v2.4.0](#v240)
- [v2.3.2](#v232)
- [v2.3.1](#v231)
- [v2.3.0](#v230)
- [v2.2.0](#v220)
- [v2.1.0](#v210)
- [v2.0.0](#v200)
- [v1.3.0](#v130)
- [v1.2.1](#v121)
- [v1.2.0](#v120)
- [v1.1.1](#v111)
- [v1.1.0](#v110)
- [v1.0.1](#v101)
- [v1.0.0](#v100)
- [v0.5.0](#v050)
- [v0.4.0](#v040)
- [v0.3.0](#v030)
- [v0.2.0](#v020)
- [v0.1.0](#v010)


## v2.5.5

Updates lookatme's CI (GitHub Actions) to use grapevine tagging

|    type | PR/ticket                                                | author                                       | description                               |
|--------:|----------------------------------------------------------|----------------------------------------------|-------------------------------------------|
| feature | [#198](https://github.com/d0c-s4vage/lookatme/issue/198) | [@d0c-s4vage](https://github.com/d0c-s4vage) | Adds grapevine tagging to CI              |

## v2.5.0

Adds the `--tutorial` CLI option.

|    type | PR/ticket                                                | author                                       | description                               |
|--------:|----------------------------------------------------------|----------------------------------------------|-------------------------------------------|
| feature | [#169](https://github.com/d0c-s4vage/lookatme/issue/169) | [@d0c-s4vage](https://github.com/d0c-s4vage) | Adds the `--tutorial` CLI option          |
|     bug | [#168](https://github.com/d0c-s4vage/lookatme/issue/168) | [@d0c-s4vage](https://github.com/d0c-s4vage) | Adds documentation for progressive slides |

## v2.4.1

Bug fix - theme and style override precedence issues. The CLI params `--theme`
and `--style` and other general style precedence issues are fixed.

| type | PR/ticket                                               | author                                       | description                                                       |
|-----:|---------------------------------------------------------|----------------------------------------------|-------------------------------------------------------------------|
|  bug | [#123](https://github.com/d0c-s4vage/lookatme/pull/123) | [@d0c-s4vage](https://github.com/d0c-s4vage) | Fixes CLI `--theme`, `--style`, and general style override issues |

## v2.4.0

Bug fixes, new features, new CI, getting ready for v3.0.

|    type | PR/ticket                                                 | author                                       | description                                                      |
|--------:|-----------------------------------------------------------|----------------------------------------------|------------------------------------------------------------------|
| feature | [!124](https://github.com/d0c-s4vage/lookatme/pull/124)   | [@agateau](https://github.com/agateau)       | Adds support for progressive slides with `<!-- stop -->` markers |
|     bug | [!125](https://github.com/d0c-s4vage/lookatme/pull/125)   | [@agateau](https://github.com/agateau)       | Fixes conflicting CLI `-s` arguments                             |
|     bug | [!133](https://github.com/d0c-s4vage/lookatme/pull/133)   | [@AMDmi3](https://github.com/AMDmi3)         | Excludes tests dir from packages                                 |
|     bug | [#126](https://github.com/d0c-s4vage/lookatme/issues/126) | [@d0c-s4vage](https://github.com/d0c-s4vage) | Fix unit test failues                                            |
|     bug | [!141](https://github.com/d0c-s4vage/lookatme/pull/141)   | [@corydodt](https://github.com/corydodt)     | Fix click requirements range                                     |
| feature | [!150](https://github.com/d0c-s4vage/pull/150)            | [@d0c-s4vage](https://github.com/d0c-s4vage) | New CI that uses GitHub actions                                  |
|     bug | [!151](https://github.com/d0c-s4vage/pull/151)            | [@d0c-s4vage](https://github.com/d0c-s4vage) | Fix linter errors                                                |


## v2.3.2

Fixes a problem in generating default schema values. This is most visible in the
style defaults, such as the margin and padding.

| type | ticket                                                    | description                    |
|-----:|-----------------------------------------------------------|--------------------------------|
|  bug | [#117](https://github.com/d0c-s4vage/lookatme/issues/117) | Fixes default style generation |


## v2.3.1

Makes lookatme compatible with marshmallow `>= 13.12.1`

|    type | ticket                                                    | description                                                   |
|--------:|-----------------------------------------------------------|---------------------------------------------------------------|
|     bug | [#114](https://github.com/d0c-s4vage/lookatme/issues/114) | Makes lookatme compatible with the latest marshmallow version |

## v2.3.0

Makes the user aware of any new, not-already-manually-approved extensions
that the source markdown wants to load.

Also checks all loaded extensions for a `user_warnings` function that returns
a list of messages to display to the user before using the extension.

Adds new `-i`, `--safe`, and `--no-ext-warn` command-line arguments.

|    type | ticket                                                    | description                                                   |
|--------:|-----------------------------------------------------------|---------------------------------------------------------------|
| feature | [#109](https://github.com/d0c-s4vage/lookatme/issues/109) | More robust extension handling, does not auto-load by default |

## v2.2.0

Removes copyrighted image, adds `-e` and `--exts` options

|    type | ticket                                                    | description                         |
|--------:|-----------------------------------------------------------|-------------------------------------|
| feature | [#103](https://github.com/d0c-s4vage/lookatme/issues/103) | Adds ability to pre-load extensions |
|     bug | [#107](https://github.com/d0c-s4vage/lookatme/issues/107) | Removes copyrighted image           |


## v2.1.0

Adds customizable slide margins and paddings

|    type | ticket                                                  | description                                 |
|--------:|---------------------------------------------------------|---------------------------------------------|
| feature | [#95](https://github.com/d0c-s4vage/lookatme/issues/95) | Make slide padding and margins customizable |

## v2.0.0

Changes `render_text` to be able to support widgets instead of only text
attributes. This is a breaking change to the interface of `render_text`.
Plugins that relied on `render_text` will need to be updated.

|    type | ticket                                                    | description                                                    |
|--------:|-----------------------------------------------------------|----------------------------------------------------------------|
| feature | [#101](https://github.com/d0c-s4vage/lookatme/issues/101) | Inline render functions should be able to return urwid Widgets |

## v1.3.0

Vertical scrolling on overflowed slides now works, added `--single` and `--one`
command-line options and hrule rendering.

|    type | ticket                                                  | description                                             |
|--------:|---------------------------------------------------------|---------------------------------------------------------|
| feature | [#96](https://github.com/d0c-s4vage/lookatme/issues/96) | Add new cmd-line option to force single slide rendering |
| feature | [#91](https://github.com/d0c-s4vage/lookatme/issues/91) | Single slide                                            |
| feature | [#29](https://github.com/d0c-s4vage/lookatme/issues/29) | Slides should be vertically scrollable                  |

## v1.2.1

Fixes numbered lists and general list formatting.

| type | ticket                                                  | description          |
|-----:|---------------------------------------------------------|----------------------|
|  bug | [#86](https://github.com/d0c-s4vage/lookatme/issues/93) | Fixes numbered lists |

## v1.2.0

Adds `terminal-ex` mode to embedded terminal code blocks.

| type | ticket                                                  | description             |
|-----:|---------------------------------------------------------|-------------------------|
|  bug | [#86](https://github.com/d0c-s4vage/lookatme/issues/86) | Adds `terminal-ex` mode |

## v1.1.1

Fixed keypress handling - pressing the "up" key works now

| type | ticket                                                  | description          |
|-----:|---------------------------------------------------------|----------------------|
|  bug | [#84](https://github.com/d0c-s4vage/lookatme/issues/84) | Fixes keypress issue |

## v1.1.0

Added file loader builtin extension

|    type | ticket                                                  | description                |
|--------:|---------------------------------------------------------|----------------------------|
| feature | [#81](https://github.com/d0c-s4vage/lookatme/issues/81) | Adds file loader extension |

## v1.0.1

Fixed unicode rendering inside Terminals

| type | ticket                                                  | description              |
|-----:|---------------------------------------------------------|--------------------------|
|  bug | [#78](https://github.com/d0c-s4vage/lookatme/issues/78) | Unicode rendering errors |

## v1.0.0

Fixed error handling. Code is pretty stable.

| type | ticket                                                  | description           |
|-----:|---------------------------------------------------------|-----------------------|
|  bug | [#75](https://github.com/d0c-s4vage/lookatme/issues/75) | Better error handling |


## v0.5.0

Adds version flag, license, code of conduct

|    type | ticket                                                  | description          |
|--------:|---------------------------------------------------------|----------------------|
| feature | [#67](https://github.com/d0c-s4vage/lookatme/issues/67) | Adds version flag    |
| feature |                                                         | Adds code of conduct |
|     bug | [#66](https://github.com/d0c-s4vage/lookatme/issues/66) | Adds missing license |


## v0.4.0

Adds stylable meta field values (title, author, date) and smart slide splitting.

|    type | ticket                                                  | description                |
|--------:|---------------------------------------------------------|----------------------------|
| feature | [#14](https://github.com/d0c-s4vage/lookatme/issues/14) | Adds stylable meta values  |
| feature | [#30](https://github.com/d0c-s4vage/lookatme/issues/30) | Adds smart slide splitting |
|     bug | [#53](https://github.com/d0c-s4vage/lookatme/issues/53) | Dump unicode styles YAML   |
|     bug | [#32](https://github.com/d0c-s4vage/lookatme/issues/32) | Fix newline bug            |
|     bug | [#57](https://github.com/d0c-s4vage/lookatme/issues/57) | Fix empty code block bug   |

## v0.3.0

Large efforts around contrib extensions and their documentation. Created the
[lookatme.contrib-template](https://github.com/d0c-s4vage/lookatme.contrib-template)
as well.

|    type | ticket                                                  | description                                                  |
|--------:|---------------------------------------------------------|--------------------------------------------------------------|
| feature | [#23](https://github.com/d0c-s4vage/lookatme/issues/23) | Adds contrib extension documentation                         |
| feature | [#46](https://github.com/d0c-s4vage/lookatme/issues/46) | Lets inline markdown rendering be extensible                 |
| feature | [#54](https://github.com/d0c-s4vage/lookatme/issues/54) | Changes the expected contrib namespace to `lookatme.contrib` |

## v0.2.0

Major efforts include adding clickable links and gracefully handling invalid
markdown code-block languages.

|    type | ticket                                                  | description                       |
|--------:|---------------------------------------------------------|-----------------------------------|
| feature | [#16](https://github.com/d0c-s4vage/lookatme/issues/16) | Added clickable links             |
|     bug | [#45](https://github.com/d0c-s4vage/lookatme/issues/45) | Handle invalid code langs         |
|     bug | [#50](https://github.com/d0c-s4vage/lookatme/issues/50) | Specify Python >= 3.3 requirement |  |

## v0.1.0

Major efforts include: light theme, documentation

|    type | ticket                                                  | description                   |
|--------:|---------------------------------------------------------|-------------------------------|
| feature | [#2](https://github.com/d0c-s4vage/lookatme/issues/2)   | Added documentation           |
|     bug | [#40](https://github.com/d0c-s4vage/lookatme/issues/40) | Updated styling               |
|     bug | [#42](https://github.com/d0c-s4vage/lookatme/issues/42) | Added code coverage           |
|     bug | [#37](https://github.com/d0c-s4vage/lookatme/issues/37) | Added description to setup.py |
|     bug | [#39](https://github.com/d0c-s4vage/lookatme/issues/39) | Fixes pygments Urwid renderer |
