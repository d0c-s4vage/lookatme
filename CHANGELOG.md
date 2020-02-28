# Changelog

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
