# JavaScript to Python

A growing Rosetta stone. Every PR that introduces something with a JS analogue
adds rows here. If you read one file in this repo twice, make it this one.

## Tooling

| JavaScript | Python | Notes |
|---|---|---|
| `nvm` | `uv python` | uv downloads and pins interpreters itself |
| `.nvmrc` | `.python-version` | |
| `npm` | `uv` | |
| `npx` | `uv run` | |
| `package.json` | `pyproject.toml` | `pyproject.toml` is a **language standard** (PEP 621), not one tool's private format |
| `package-lock.json` | `uv.lock` | Both committed |
| `node_modules/` | `.venv/` | `.venv` also contains the interpreter itself |
| `engines.node` | `requires-python` | Python actually enforces it |
| `dependencies` | `[project] dependencies` | |
| `devDependencies` | `[dependency-groups] dev` | Added in PR-002 |
| `bin` | `[project.scripts]` | Added in PR-020 |
| `eslint` + `prettier` | `ruff` | One tool for both. PR-002 |
| `tsc` | `mypy` | PR-003 |
| `jest` / `vitest` | `pytest` | PR-004 |
| `tsup` / `esbuild` (library build) | `uv_build` / `hatchling` | Declared, never invoked by you |

## Language

| JavaScript | Python | Notes |
|---|---|---|
| `{ }` blocks | Indentation | Four spaces. Grammar, not style. |
| `//` | `#` | |
| `` `a ${b}` `` | `f"a {b}"` | The `f` prefix is required |
| `null` | `None` | Python has no separate `undefined` |
| `undefined` | *(does not exist)* | One absent-value type, not two |
| `import { y } from "x"` | `from x import y` | |
| `import * as x from "x"` | `import x` | |
| `index.ts` | `__init__.py` | Mandatory; its existence is what makes a package |
| `require.main === module` | `__name__ == "__main__"` | |
| `function f(): T` | `def f() -> T:` | |
| JSDoc comment | `"""docstring"""` | A real runtime value, not a comment |
| `.d.ts` | inline hints + `py.typed` | Types live in the source; the marker grants permission to read them |
| `Symbol.iterator` | `__iter__` and friends | "Dunder" methods |
| `interface` (structural) | `typing.Protocol` | PR-022. This is the one that will feel like home. |
| `class` (nominal) | `abc.ABC` | PR-022 |

## Habits to unlearn

- **`source .venv/bin/activate`** — works, but `uv run` makes it unnecessary and
  is harder to get wrong. An activated environment is invisible global state
  following your shell around.
- **`pip install X`** — installs into whatever Python happens to be first on
  `PATH`, which is rarely the one you meant. Use `uv add X`, which records the
  dependency in `pyproject.toml` at the same time. It is `npm install --save`,
  and there is no unsaved variant.
- **Running a file by path** — `python src/quantlab/__main__.py` bypasses the
  package machinery and breaks relative imports. Use `python -m quantlab`.
- **`float` for money** — see PR-008. This one will cost you real numbers.
