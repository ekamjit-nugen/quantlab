# PR-001 — Project scaffold, `src` layout, `python -m quantlab`

> **How to read these docs.** Every PR in this repo ships one of these. It
> assumes you can already program — it does not explain what a function is. It
> explains what *Python* does, why *this* package was chosen, what each line
> means, and what the JavaScript equivalent would be.

---

## 1. What this PR adds

An empty but correctly structured Python project that installs, imports and
runs. Nothing domain-specific yet — just the skeleton every later PR builds on.

| File | Purpose |
|---|---|
| `.python-version` | Which Python version this project uses. The `.nvmrc`. |
| `pyproject.toml` | Project metadata + dependencies. The `package.json`. |
| `uv.lock` | Exact resolved versions. The `package-lock.json`. **Committed.** |
| `.gitignore` | What git must never track. |
| `src/quantlab/__init__.py` | Makes the folder a package. The `index.ts`. |
| `src/quantlab/__main__.py` | Runs on `python -m quantlab`. |
| `src/quantlab/py.typed` | Marker: "this package ships real type hints." |
| `docs/prs/` | These teaching documents. |
| `docs/js-to-python.md` | A growing JS→Python Rosetta stone. |

Verified working:

```
$ uv run python -m quantlab
quantlab 0.1.0
```

## 2. Why now

Nothing else can exist until imports resolve. Python's single biggest beginner
trap is *import errors caused by project layout*, and the `src/` layout used
here eliminates an entire class of them — see §7.

## 3. Commands run

### 3.1 Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

`uv` manages Python versions, virtual environments, dependencies and script
running. One tool replacing what is `nvm` + `npm` + `npx` in your world.

The curl flags, individually:

| Flag | Meaning |
|---|---|
| `-L` | Follow redirects. The short URL redirects to GitHub releases. |
| `-s` | Silent — suppress the progress meter. |
| `-S` | *Re-enable* error messages, which `-s` would otherwise hide. `-sS` together means "quiet, but shout if you break". |
| `-f` | Fail on HTTP errors instead of saving the error page as if it were the file. |

`| sh` pipes the downloaded script into the shell to execute it.

uv installs to `~/.local/bin`. It touches nothing system-wide, and it does not
interfere with the Homebrew Python already on this machine.

### 3.2 Create the project

```bash
uv init --lib --name quantlab --python 3.13 ~/Projects/quantlab
```

| Part | Meaning |
|---|---|
| `uv init` | Scaffold a new project. Equivalent to `npm init`. |
| `--lib` | Build a **library** (importable package under `src/`) rather than an **app** (a bare `main.py`). We want a library because `quantlab` will be imported by the CLI, the API, the tests and eventually the agents. |
| `--name quantlab` | The package name — what `import quantlab` will find. |
| `--python 3.13` | Pin the interpreter. Writes `.python-version`. |
| *last argument* | The directory to create. |

**Why 3.13 and not 3.14?** This machine has 3.14 installed. It is too new for
some of the quantitative libraries this project will need later (Phase 7's data
stack in particular). uv downloads and manages 3.13 independently, so pinning
costs nothing.

`uv init` also runs `git init` for you.

### 3.3 Install dependencies and create the environment

```bash
uv sync
```

Reads `pyproject.toml`, resolves versions, writes `uv.lock`, creates `.venv/`,
and installs this project into it in editable mode. This is `npm install`.

Actual output on first run:

```
Using CPython 3.13.9 interpreter at: /opt/homebrew/opt/python@3.13/bin/python3.13
Creating virtual environment at: .venv
Resolved 1 package in 21ms
   Building quantlab @ file:///Users/ekamjitsingh/Projects/quantlab
      Built quantlab @ file:///Users/ekamjitsingh/Projects/quantlab
Installed 1 package in 2ms
 + quantlab==0.1.0 (from file:///Users/ekamjitsingh/Projects/quantlab)
```

Note the last line: **quantlab installs itself**. That is not a quirk, it is the
point. Your own package is a dependency of your own project, installed in
editable mode (a link to `src/`, not a copy), which is why `import quantlab`
works from tests, from the REPL, and from anywhere else. In JS you would fake
this with a path alias in `tsconfig.json`; Python does it properly.

> **The mental model that matters.** `.venv/` is `node_modules/` — a folder of
> this project's dependencies, isolated from every other project. The difference
> is that `.venv/` also contains a copy of the Python **interpreter**. So "which
> Python am I running" and "which packages can I see" are the same question.
> That coupling is the thing that makes virtual environments feel stranger than
> `node_modules` at first. Once you accept it, it stops being confusing.

### 3.4 Run it

```bash
uv run python -m quantlab
```

`uv run <cmd>` executes `<cmd>` with `.venv` active, without you having to
"activate" anything. It is `npx`. You will type this constantly.

You may see older tutorials say `source .venv/bin/activate` first. That still
works, but `uv run` makes it unnecessary and is harder to get wrong — an
activated environment is invisible global state that follows your shell around.

`python -m quantlab` means "find the **module** named `quantlab` and run its
`__main__.py`". The `-m` flag means module, not file path. Running
`python src/quantlab/__main__.py` directly would **fail**, because that bypasses
the package machinery and `from quantlab import ...` would not resolve.

## 4. Packages introduced

| Package | What it is | Why this one | JS equivalent |
|---|---|---|---|
| **uv** `0.12.18` | Python version + venv + dependency + task manager | Replaces pyenv/venv/pip/pip-tools/poetry/pipx with one very fast tool. The 2026 default. | `nvm` + `npm` + `npx` |
| **uv_build** | Build backend — turns `src/` into an installable wheel | uv's own backend, now its default. Zero config, no extra download. | `tsup` / `esbuild` for a library build |

Note that `uv_build` appears in `pyproject.toml` but you never invoke it
yourself. It is *declared*, and the packaging machinery calls it on your behalf.
There is no JS equivalent to this indirection — it is how Python keeps "your
project" separate from "the tool that packages your project", so that anyone can
build your package without having your toolchain installed.

## 5. The code, line by line

### `pyproject.toml`

```toml
[project]
name = "quantlab"
version = "0.1.0"
description = "A market-research and backtesting toolkit"
readme = "README.md"
authors = [{ name = "ekam", email = "ekam.nugen@gmail.com" }]
requires-python = ">=3.13"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.18,<0.13.0"]
build-backend = "uv_build"
```

- **`[project]`** — a *table*, which is TOML's word for an object. This
  particular table is standardised by **PEP 621**, meaning every Python tool
  reads it identically. This is a real difference from `package.json`, which is
  npm's private format that other tools merely tolerate.
- **`name`** — the import name and the distribution name.
- **`version`** — your version string. Python has no built-in `npm version`
  command; you edit this by hand for now. PR-020 fixes that.
- **`readme`** — which file a package index should display.
- **`authors`** — a TOML *array of tables*: a list, each element an object.
  uv pre-filled it from your global git config.
- **`requires-python = ">=3.13"`** — refuses to install on older interpreters.
  This is `engines.node`, except it is actually enforced rather than warned about.
- **`dependencies = []`** — runtime dependencies. Empty for now. This is
  `package.json` → `dependencies`. There is no `devDependencies` key here;
  dev tools go in a different table, which PR-002 introduces.
- **`[build-system]`** — tells any packaging tool *how* to build this project.
- **`requires`** — install these into a temporary isolated environment to do the
  build. The version range `>=0.12.18,<0.13.0` is Python's spelling of `^0.12.18`.
- **`build-backend`** — the Python import path to the object that performs the
  build.

### `src/quantlab/__init__.py`

```python
"""quantlab - a market-research and backtesting toolkit."""

__version__ = "0.1.0"
```

- **Line 1** is a **module docstring**. A string literal as the very first
  statement in a file becomes that module's documentation, readable at runtime
  as `quantlab.__doc__`. JS has no real equivalent — it is closest to a JSDoc
  block, except it is a genuine runtime value rather than a comment.
- **Line 3** defines a module-level variable. The double-underscore name is a
  **dunder** ("double underscore") — the convention for names that Python or its
  ecosystem treats specially. `__version__` is the near-universal convention for
  a package's version.

**The critical thing about this file is its existence.** `src/quantlab/` is a
package *because this file is here*. `import quantlab` works for the same
reason. It is `index.ts`, but mandatory and usually nearly empty. Exercise 1
below makes you feel what happens without it.

### `src/quantlab/__main__.py`

```python
"""Entry point: `python -m quantlab` runs this file."""

from quantlab import __version__


def main() -> None:
    """Print the installed version and exit."""
    print(f"quantlab {__version__}")


if __name__ == "__main__":
    main()
```

- **`from quantlab import __version__`** — import one name out of the `quantlab`
  package. Equivalent to `import { __version__ } from "quantlab"`. The plain
  form `import quantlab` (then `quantlab.__version__`) is equivalent to
  `import * as quantlab from "quantlab"`.
- **`def main() -> None:`** — define a function named `main` taking no
  arguments. `-> None` is a **return type annotation**: this function returns
  nothing. `None` is Python's `null`. Python has only one such value — there is
  no separate `undefined`, which removes a whole category of JS bug.
- **The `"""..."""` inside the function** is a **function docstring**, attached
  to `main.__doc__`. Same idea as the module docstring, one level down.
- **`print(f"quantlab {__version__}")`** — `f"..."` is an **f-string** (format
  string). Anything inside `{}` is evaluated and interpolated. It is a template
  literal with `{}` in place of `${}`. The `f` prefix is required; without it
  you get the literal text `{__version__}`.
- **`if __name__ == "__main__":`** — **the single most confusing line in Python
  for newcomers, so read this twice.**

  Every module has a `__name__` variable. When a module is **imported**,
  `__name__` is its import path — here, `"quantlab.__main__"`. When a module is
  **run directly**, `__name__` is the literal string `"__main__"`.

  So the guard means: *"only do this when I am being run, not when I am being
  imported."* The JS equivalent is `if (require.main === module)`.

  Without the guard, merely importing this file would print output — which
  breaks tests, breaks tooling that introspects your modules, and breaks
  `multiprocessing` outright on macOS and Windows (Phase 6 will show you exactly
  how). Exercise 2 makes you watch it happen.

- **Two blank lines** between top-level definitions is not a preference. It is
  PEP 8, and PR-002's formatter will enforce it mechanically.

### `src/quantlab/py.typed`

An **empty file**. Its presence is a flag (PEP 561) telling type checkers "this
package's type hints are real, trust them." Without it, `mypy` silently ignores
your annotations when another project imports you.

Shipping `.d.ts` files is the JS analogue — except Python's types live inline in
the source, so there is nothing to ship, only permission to look.

### `.gitignore`

```gitignore
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info
.venv
.mypy_cache/
.ruff_cache/
.pytest_cache/
.DS_Store
```

- **`__pycache__/`** and **`*.py[oc]`** — Python compiles each module to
  bytecode and caches it here so the next import is faster. `[oc]` is a glob
  character class matching `.pyo` or `.pyc`. Generated, never edited, never
  committed. There is no JS equivalent.
- **`build/`, `dist/`, `wheels/`, `*.egg-info`** — packaging output.
- **`.venv`** — never commit the environment. This is `node_modules/`.
- **The `*_cache/` entries** — tool caches from PR-002 onward.

**`uv.lock` is deliberately *not* ignored.** Commit it, exactly as you commit
`package-lock.json`.

## 6. New syntax introduced

| Syntax | Meaning | JS analogue |
|---|---|---|
| `"""docstring"""` | First-statement string becomes documentation | JSDoc comment (but a real runtime value) |
| `f"text {expr}"` | Interpolated string | `` `text ${expr}` `` |
| `def name() -> T:` | Function with return-type annotation | `function name(): T` |
| `None` | The absence of a value | `null` (Python has no `undefined`) |
| `from X import Y` | Named import | `import { Y } from "X"` |
| `import X` | Namespace import | `import * as X from "X"` |
| `__dunder__` | Name with special meaning to the runtime | `Symbol.iterator`, roughly |
| `#` | Comment | `//` |
| Indentation | Block structure | `{ }` |

**On indentation.** It is not a style preference, it is the grammar. Four
spaces, never tabs; mixing them is a hard error. Coming from JS this is the
adjustment that takes longest to stop noticing, and the formatter added in
PR-002 means you will stop thinking about it within a week.

**On semicolons.** Legal, but never used. Line ends are statement ends.

## 7. Other ways this could have been written

### Project layout: `src/` vs flat

We used `src/quantlab/`. The common alternative is `quantlab/` at the repo root.

Flat layout has a subtle and vicious failure mode. When you run tests from the
repo root, Python puts the current directory first on the import path, so
`import quantlab` finds the **source folder** rather than the **installed
package**. Your tests then pass against code that would break the moment anyone
installed it — a missing file in `pyproject.toml`, a missing `__init__.py`, a
data file you forgot to declare. `src/` makes that mistake impossible, because
the source is not importable from the root at all.

Use `src/`. Always. This is the one layout decision with no real trade-off.

### Dependency manager

| Option | Verdict |
|---|---|
| `pip` + `venv` | Stdlib, always available, verbose, **no lockfile**. Fine to understand, not to use. |
| `poetry` | Good, popular, noticeably slower, and its config predates PEP 621 so it looks different from everyone else's. |
| `pdm` | Standards-compliant, smaller community. |
| `pipenv` | Effectively abandoned. Avoid. |
| `conda` / `mamba` | Its own universe. Necessary for some heavy scientific stacks, overkill here. |
| **`uv`** | **Chosen.** Fastest by a wide margin, PEP 621 native, does versions + venvs + deps + tool running. |

### Build backend

`uv_build` (chosen, uv's default), `hatchling` (the most common general choice),
`setuptools` (the oldest, most configurable, most painful), `flit` (minimal),
`maturin` (needed only when you add Rust — which Phase 9 will).

### Declaring the version

We hard-coded `version` in **two** places: `pyproject.toml` and
`__init__.py`. These will drift. The alternatives are `hatch-vcs` (derive it
from git tags) or reading it at runtime with
`importlib.metadata.version("quantlab")`.

We are doing it the duplicated way **on purpose**, so that you feel the problem
before PR-020 shows you the fix. Noticing the drift yourself is the lesson.

### Entry point style

Instead of `__main__.py`, you can declare `[project.scripts]` in
`pyproject.toml` and get a real `quantlab` command on `PATH`. That is
`package.json` → `bin`. PR-020 adds it. Both can coexist.

## 8. Exercises

**1 — Break the package.** Delete `src/quantlab/__init__.py`, then run
`uv run --no-sync python -m quantlab`. You get:

```
ImportError: cannot import name '__version__' from 'quantlab' (unknown location)
```

The interesting part is **`(unknown location)`**. Python did *not* say "no
module named quantlab" — it found something called `quantlab` and it was empty.
That is because a directory without `__init__.py` still counts as a **namespace
package** (PEP 420): importable, but with no code in it. This is why a missing
`__init__.py` produces a baffling error about a missing *name* rather than a
clear error about a missing *module*. You will hit this again. Restore the file.

**2 — Break the guard.** Remove the `if __name__ == "__main__":` line and
de-indent `main()` so it runs unconditionally. Now run
`uv run --no-sync python -c "import quantlab.__main__"`. It prints the version —
merely *importing* the module caused a side effect. Put the guard back and run
the same command: silence. That contrast is the whole point of the guard.

**3 — Add a return value.** Write `banner() -> str` that *returns* the version
string instead of printing it, and have `main()` print its result. Sit with the
difference between `-> str` and `-> None`; PR-003's type checker will start
holding you to it.

## 9. Merge checklist

- [x] `uv run python -m quantlab` prints `quantlab 0.1.0`
- [x] `uv.lock` committed
- [x] This document written
- [x] `docs/js-to-python.md` seeded from §6
- [x] `docs/prs/README.md` has a row for PR-001

## 10. What PR-002 will add

`ruff` — linting and formatting. It will reformat some of the code written here,
and the diff it produces is itself a lesson in what idiomatic Python looks like.
