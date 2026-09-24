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
| `devDependencies` | `[dependency-groups] dev` | PEP 735. Sits *outside* `[project]` — dev deps are not package metadata. PR-002 |
| `bin` | `[project.scripts]` | Added in PR-020 |
| `eslint` | `ruff check` | PR-002 |
| `prettier` | `ruff format` | Same binary as the linter. PR-002 |
| `.eslintrc` + `.prettierrc` | `[tool.ruff]` in `pyproject.toml` | Every tool namespaces under `[tool.*]`. No config litter. |
| `tsc` | `mypy` | PR-003. But see the strictness note below. |
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
| `private` | *(does not exist)* | `_single` is convention; `__double` is name mangling, not access control |
| `#private` (true privacy) | *(no equivalent)* | Everything is reachable in Python |
| `f(x, bucket = [])` — fresh array per call | `def f(x, bucket=[])` — **shared** across calls | Default evaluated once at `def` time. Use `=None`. PR-002 |
| `Array`, `Object` are protected-ish | `list`, `dict`, `id`, `type` are plain names | You can shadow them by accident. PR-002 |
| `===` vs `==` (coercion) | `is` vs `==` (identity vs value) | Not the same distinction. Python's `==` never coerces. Always `is None`. |
| `string \| null` | `str \| None` | Same syntax. Older code writes `Optional[str]`. PR-003 |
| `strictNullChecks` | on under `strict = true` | PR-003 |
| `@ts-ignore` | `# type: ignore[code]` | `ignore-without-code` bans the bare form, like preferring `@ts-expect-error`. PR-003 |
| hover to see a type | `reveal_type(x)` | Works in CI and in a diff, not just an editor. Does not exist at runtime. PR-003 |
| `let` / block scope | *(none)* | Function scope only. A name bound inside `if` is visible after it. PR-003 |
| `T[]` is **covariant** (unsound) | `list[T]` is **invariant** | Python is stricter here. Use `Sequence[T]` for read-only params. PR-003 |
| `void` | `-> None` | Every function returns something; no `return` means it returns `None` |
| types erased at compile time | annotations **kept** at runtime | The key divergence from TS. `f.__annotations__` is real data, which is how FastAPI, Pydantic and PR-011's tool schemas work. |

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

## Underscore patterns

Four patterns that look alike. Only two are real language features.

| Pattern | Meaning | Enforced? |
|---|---|---|
| `__both__` | dunder — a name Python or the ecosystem already defines | Sometimes |
| `_single` | "internal, don't touch" | No. Convention only. |
| `__leading` *inside a class* | name mangling: rewritten to `_ClassName__leading` | **Yes** |
| `trailing_` | avoids clashing with a keyword (`class_`, `id_`) | No |

**The rule:** you almost never *invent* a dunder, you *implement* ones that
already exist. PEP 8 reserves `__x__` names for the language itself.

See [PR-001 §10.1-10.3](prs/PR-001-scaffold.md) for the full explanation and the
demonstration of name mangling eating a module name.

## Strictness is not the same dial

`tsconfig` `strict: false` still checks your code — it just infers `any` more
and stops complaining about `null`.

**mypy's default does not check unannotated function bodies at all.** It skips
them, and their return type becomes `Any`, which then silences checks in every
caller. That is gradual typing, designed for adding types to a large untyped
codebase over years.

You are starting from zero, so `strict = true` from PR-003 onward, permanently.
See [PR-003 §3.3](prs/PR-003-mypy.md) for the file that default mypy declares
clean while it concatenates an int and a string.
