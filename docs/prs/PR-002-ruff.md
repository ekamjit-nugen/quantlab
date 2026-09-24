# PR-002 — `ruff`: linting and formatting, plus a single-source version

> Every output quoted in this document was produced by running against this
> repository. Nothing here is predicted.

---

## 1. What this PR adds

Two things:

1. **`ruff`** as a dev dependency, configured with a real rule set. One tool
   doing what `eslint` + `prettier` + several plugins do in JavaScript.
2. **The version fix** from [PR-001 §10.4](PR-001-scaffold.md) — pulled forward
   from PR-020, because leaving a known bug in `main` for eighteen PRs to
   preserve a teaching beat is the wrong trade.

| File | Change |
|---|---|
| `pyproject.toml` | `[dependency-groups] dev`, `[tool.ruff]*` config, 32 lines |
| `src/quantlab/__init__.py` | Version now read from package metadata |
| `uv.lock` | ruff pinned at 0.16.8 |
| `docs/prs/PR-001-scaffold.md` | Reformatted by ruff — see §3.5 |

## 2. Why now

**The formatter comes before the code, not after.** Adding it at PR-050 would
mean one enormous reformat commit polluting the history of fifty files. Adding
it at PR-002 means every line ever written in this repo was written under it,
and you never think about layout again.

For someone coming from JavaScript this matters more than usual: Python's
indentation *is* its grammar, and having a tool that fixes layout mechanically
removes the one genuinely annoying part of the transition.

## 3. Commands run

### 3.1 Add ruff as a development dependency

```bash
uv add --dev ruff
```

- `uv add` — install a package **and record it in `pyproject.toml`**. This is
  `npm install --save`. There is no unsaved variant in uv, which is a deliberate
  and good design choice: an installed-but-undeclared dependency is always a
  bug.
- `--dev` — put it in the dev group rather than runtime dependencies. This is
  `npm install --save-dev`.

What it wrote:

```toml
[dependency-groups]
dev = [
    "ruff>=0.16.8",
]
```

`[dependency-groups]` is **PEP 735**, a relatively recent standard. Note that it
sits *outside* `[project]` — dev dependencies are explicitly not part of your
published package, so they are not part of project metadata. In `package.json`,
`devDependencies` sits alongside `dependencies` as a sibling key; Python draws
the line harder.

### 3.2 Lint

```bash
uv run ruff check .
```

Reports problems. Add `--fix` to apply the automatic ones:

```bash
uv run ruff check --fix .
```

### 3.3 Format

```bash
uv run ruff format .
```

Rewrites layout. Use `--diff` to preview without writing, or `--check` to fail
without writing (what CI will use in PR-006):

```bash
uv run ruff format --diff .
```

**`check` and `format` are different jobs.** `format` only touches layout —
line breaks, quotes, spacing. `check` finds *problems* — unused imports,
shadowed builtins, real bugs. In JavaScript terms, `format` is prettier and
`check` is eslint. ruff is both programs behind one binary.

### 3.4 What ruff actually catches

The code in this repo passes everything, which teaches you nothing. So here is
ruff against a deliberately terrible file:

```python
import os
from typing import Dict, List
import sys


def summarise(values: List[int], seen: Dict[str, int] = {}) -> bool:
    list = [v for v in values if v > 0]
    if len(list) == True:
        return True
    else:
        return False


path = os.path.join("data", "bars.csv")
```

Fourteen lines. **Thirteen errors, across nine rule families:**

| Code | Says | Why it matters |
|---|---|---|
| `D100` / `D103` | Missing docstring in module / function | Docstrings are runtime values here, not comments |
| `I001` | Import block is un-sorted | stdlib, third-party, local — in that order, alphabetical within groups |
| `UP035` / `UP006` | `typing.Dict` is deprecated, use `dict` | See §6.3 |
| `F401` | `sys` imported but unused | A real bug or real dead code, always |
| `B006` | Mutable data structure as argument default | **The single worst Python gotcha. See below.** |
| `A001` | Variable `list` is shadowing a builtin | **Also worse than it looks. See below.** |
| `SIM103` | Return the condition directly | `return len(x) > 0`, not if/else |
| `E712` | Avoid equality comparison to `True` | `if x:`, not `if x == True:` |
| `PTH118` | `os.path.join()` should be `Path` with `/` | Modern Python is `Path("data") / "bars.csv"` |

```
Found 13 errors.
[*] 4 fixable with the `--fix` option (3 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

Note the distinction between **fixable** and **unsafe-fixable**. ruff will only
auto-apply changes it is certain preserve behaviour. Removing an unused import
is safe; rewriting an if/else into a bare return could change semantics if the
values are not actually booleans, so that one needs `--unsafe-fixes` and your
eyeballs.

#### B006 — the mutable default argument

This is the one that will bite you, because it behaves unlike anything in
JavaScript:

```python
def add(item, bucket=[]):  # evaluated ONCE, at def time
    bucket.append(item)
    return bucket


print("call 1:", add("a"))
print("call 2:", add("b"))
print("call 3:", add("c"))
```
```
call 1: ['a']
call 2: ['a', 'b']
call 3: ['a', 'b', 'c']
```

**The default value is evaluated once, when the `def` statement runs — not on
each call.** So every call that omits `bucket` shares *the same list object*.
In JavaScript, `function add(item, bucket = [])` creates a fresh array per call;
Python does not.

The fix is always the same shape:

```python
def add(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

This has caused production bugs in every Python codebase that did not lint for
it. Now yours does.

#### A001 — builtins are just names

```python
print("before:", list((1, 2)))
list = [9, 9]
list((3, 4))
```
```
before: [1, 2]
after:  'list' object is not callable
```

`list`, `dict`, `id`, `type`, `input`, `sum`, `filter` and friends are **not
keywords**. They are ordinary names in a scope you are allowed to shadow. Assign
to one and the real builtin is gone for the rest of that scope.

JavaScript protects you here — `Array` is not something you accidentally
reassign, and `const` would stop you. Python just lets it happen, quietly, and
the error surfaces somewhere else entirely. Hence the rule.

### 3.5 The one file ruff reformatted

```diff
--- docs/prs/PR-001-scaffold.md
@@
 class Account:
     def __init__(self):
-        self._soft = 1      # convention only
-        self.__hard = 2     # name-mangled
+        self._soft = 1  # convention only
+        self.__hard = 2  # name-mangled
```

Two things worth noticing.

**First: ruff formats Python code blocks inside Markdown, with no configuration
at all.** Verified on a bare file with no `pyproject.toml` present. For this
repository — where most of the teaching happens in fenced code blocks — that is
genuinely useful: the examples in the docs are held to the same standard as the
source.

**Second: I had aligned those comments by hand, and ruff undid it.** PEP 8 says
exactly two spaces before an inline comment, and the formatter is not
negotiating. This is the entire point of adopting a formatter: *you stop having
opinions about layout*, and every diff from here on contains only meaning.

The Python source files needed no changes — they were already written in ruff's
style.

## 4. Packages introduced

| Package | What it is | Why this one | JS equivalent |
|---|---|---|---|
| **ruff** `0.16.8` | Linter + formatter, written in Rust | Replaces `black` + `isort` + `flake8` + `pyupgrade` + `pydocstyle` + dozens of flake8 plugins with one binary. Typically 10-100x faster. Now the de-facto standard. | `eslint` + `prettier` in one |

ruff is a dev dependency only. It never ships with your package.

## 5. The code, line by line

### `pyproject.toml` — the ruff configuration

```toml
[tool.ruff]
line-length = 88
src = ["src", "tests"]
```

- **`[tool.ruff]`** — the `[tool.*]` namespace is where PEP 621 tells every tool
  to put its own configuration. This is why Python projects need no `.ruffrc`,
  `.eslintrc`, `.prettierrc` litter: one file, namespaced sections. It is the
  single best thing about `pyproject.toml` versus `package.json`.
- **`line-length = 88`** — the wrap column. 88 is `black`'s default and the
  community norm; PEP 8 itself says 79, which most people find too narrow.
- **`src = ["src", "tests"]`** — tells the import sorter which directories hold
  *first-party* code, so it can distinguish `import quantlab` (yours, sorted
  last) from `import httpx` (third-party, sorted middle). Without this it would
  guess.

```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors      - PEP 8 layout
    "W",    # pycodestyle warnings    - trailing whitespace, etc.
    "F",    # pyflakes                - real bugs: unused imports, undefined names
    "I",    # isort                   - import ordering
    "N",    # pep8-naming             - naming conventions
    "D",    # pydocstyle              - docstring presence and style
    "UP",   # pyupgrade               - rewrite to modern Python syntax
    "B",    # flake8-bugbear          - likely bugs and design problems
    "A",    # flake8-builtins         - shadowing builtins (list, id, type...)
    "C4",   # flake8-comprehensions   - simpler comprehensions
    "SIM",  # flake8-simplify         - redundant constructs
    "PTH",  # flake8-use-pathlib      - prefer pathlib over os.path
    "RUF",  # ruff's own rules
]
```

**Why the codes look arbitrary.** They are historical. Before ruff, each of
these was a separate `flake8` plugin with its own prefix — `flake8-bugbear`
emitted `B` codes, `flake8-simplify` emitted `SIM`, and so on. ruff
reimplemented all of them and kept the prefixes so existing `# noqa: B006`
comments across the ecosystem still work. You are looking at an archaeology
layer, not a design.

**`select` is a whitelist.** ruff's default is only `E4`, `E7`, `E9` and `F` —
deliberately minimal. Everything above is opt-in. You can also `ignore`
individual codes, and `extend-select` on top of a preset.

The set chosen here is deliberately opinionated but not hostile. Notably absent:
`ANN` (mandatory annotations everywhere — mypy does this better in PR-003),
`ERA` (flags all commented-out code — too noisy while learning), and `PL`
(pylint's rules — good, but a lot at once).

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

Which docstring *style* the `D` rules enforce. The three options are `google`
(readable, `Args:` / `Returns:` sections), `numpy` (underlined headings, common
in scientific code) and `pep257` (minimal). Google style is the most common in
application code and the easiest to read. This becomes visible in PR-007 when
functions start taking arguments.

```toml
[tool.ruff.format]
docstring-code-format = true
```

Formats Python code *inside docstrings* — doctest lines and fenced examples:

```diff
 def f():
     """Doc.
 
-    >>> x = [1,  2]
+    >>> x = [1, 2]
     """
```

This is **separate** from the Markdown formatting in §3.5, which needs no
configuration. Worth stating plainly because it is easy to assume this setting
caused that diff. It did not.

### `src/quantlab/__init__.py` — the version fix

```python
"""quantlab - a market-research and backtesting toolkit."""

from importlib.metadata import version

__version__ = version("quantlab")
```

- **`from importlib.metadata import version`** — `importlib.metadata` is
  **standard library**; no dependency added. It reads the metadata of an
  *installed* distribution.
- **`__version__ = version("quantlab")`** — looks up the installed distribution
  named `quantlab` and returns its version string. The argument is the
  *distribution* name from `[project] name`, which happens to match the import
  name here but need not in general (`pip install pillow` gives you
  `import PIL`).

**Proof that it is now a single source of truth** — bumping only
`pyproject.toml`:

```
=== prove single source: bump ONLY pyproject.toml ===
quantlab 0.2.0
=== revert ===
quantlab 0.1.0
```

The string in `__init__.py` is gone; there is exactly one place to edit.

**The gotcha you must know:** this reads *installed* metadata, so after editing
`version` in `pyproject.toml` you must re-install for the change to be visible:

```bash
uv sync
```

Editing the toml alone changes nothing at runtime until then. That surprises
people once, and only once.

**The trade-off:** it requires the package to be installed. Yours is, in
editable mode. Code run from a raw source copy with no install raises
`PackageNotFoundError`. For an application that is correct; a
widely-distributed library would wrap it in `try`/`except`.

## 6. New syntax and concepts

### 6.1 TOML nested tables

`[tool.ruff.lint.pydocstyle]` is one table, not three. The dots are the path.
The equivalent JSON is:

```json
{ "tool": { "ruff": { "lint": { "pydocstyle": { "convention": "google" } } } } }
```

TOML flattens deep nesting into readable headers. This is why Python config
tolerates depth that would be painful in `package.json`.

### 6.2 `is None` versus `== None`

Seen in the B006 fix above. Always `is None`, never `== None`. `is` compares
**identity** (the same object in memory); `==` compares **value** and can be
overridden by a class's `__eq__`. Since `None` is a singleton — exactly one
exists — identity is both correct and faster, and it cannot be subverted by a
badly-behaved object.

JavaScript's `===` versus `==` is a different distinction (type coercion), so do
not map them onto each other. Python's `==` does not coerce.

### 6.3 `list[int]` not `List[int]`

Old Python required importing capitalised aliases from `typing`:

```python
from typing import Dict, List


def f(xs: List[int]) -> Dict[str, int]: ...
```

Since 3.9 the builtins are subscriptable directly, and the `typing` aliases are
deprecated:

```python
def f(xs: list[int]) -> dict[str, int]: ...
```

You will meet the old form constantly in tutorials and Stack Overflow answers
written before 2021. `UP006` and `UP035` exist to stop you copying it. Write the
lowercase form; this project is 3.13.

## 7. Other ways this could have been written

### Linting and formatting

| Option | Verdict |
|---|---|
| `black` + `isort` + `flake8` + plugins | The previous standard. Three-plus tools, three configs, seconds per run instead of milliseconds. Still everywhere in older codebases. |
| `pylint` | Deeper semantic analysis than ruff, genuinely catches things ruff does not — but slow and famously noisy out of the box. Reasonable as a supplement later; poor as a first linter. |
| `autopep8` / `yapf` | Older formatters, configurable to a fault. The value of a formatter is that it is *not* configurable. |
| **`ruff`** | **Chosen.** One binary, one config block, near-instant, actively absorbing the rest of the ecosystem. |

### Line length

79 (PEP 8 literal), **88** (black/ruff default, chosen), 100, or 120. 88 exists
because black's author measured that it reduced total lines versus 79 without
hurting readability. Any consistent choice is fine; an inconsistent one is not.

### Version source of truth

| Approach | Source of truth | Trade-off |
|---|---|---|
| **`importlib.metadata`** (chosen) | `pyproject.toml` | Needs the package installed |
| `dynamic = ["version"]` + backend reads `__init__.py` | The code | Backend-specific config |
| `hatch-vcs` / `setuptools-scm` | Git tags | Version only exists after tagging; awkward in dirty trees |
| Hard-code in both (PR-001) | Neither | Drifts. This is the bug we just fixed. |

## 8. Exercises

1. **Watch a fix happen.** Recreate the bad file from §3.4, run
   `uv run ruff check --fix bad.py`, and diff before against after. Note which
   four of the thirteen it fixed and which nine it left — then think about why
   each of the nine needed a human.

2. **Feel the mutable default.** Run the `add(item, bucket=[])` example. Then
   apply the `None` fix and run again. This costs two minutes and inoculates you
   against a bug that has shipped to production in every large Python codebase.

3. **Break the format check.** Put six spaces before a comment in
   `__main__.py`, run `uv run ruff format --check .` (it fails, and changes
   nothing), then `uv run ruff format .` (it fixes it). That is precisely the
   pair CI will use in PR-006: `--check` in CI, plain `format` locally.

4. **Add a rule family and read the fallout.** Add `"ANN"` to `select` and run
   `check`. See what mandatory-annotation enforcement demands. Then remove it —
   PR-003's mypy does that job better, and knowing *why* you rejected a rule is
   worth more than never having tried it.

## 9. Merge checklist

- [x] `uv run ruff check .` — All checks passed
- [x] `uv run ruff format --check .` — clean
- [x] `uv run python -m quantlab` prints `quantlab 0.1.0`
- [x] Version proven single-source by bumping only `pyproject.toml`
- [x] This document written
- [x] `docs/js-to-python.md` extended
- [x] `docs/prs/README.md` updated

## 10. What PR-003 will add

`mypy --strict` — the type checker. This is the one that will feel most like
home, and the one that will do the most to teach you Python's semantics. It will
also be the first tool in this repo that genuinely rejects code you have
written.
