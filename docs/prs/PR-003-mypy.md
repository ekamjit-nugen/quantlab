# PR-003 — `mypy --strict`: the type checker

> Every output quoted in this document was produced by running against this
> repository. Nothing here is predicted.

---

## 1. What this PR adds

`mypy` as a dev dependency, configured in strict mode plus three extra error
codes. This is the tool that will feel most like home coming from TypeScript —
and the one that will teach you the most about Python's actual semantics.

| File | Change |
|---|---|
| `pyproject.toml` | `[tool.mypy]` config, 12 lines |
| `uv.lock` | mypy 2.3.1 + `mypy-extensions`, `pathspec`, `typing-extensions` |

No source changes. The existing code already passes strict:

```
Success: no issues found in 2 source files
```

## 2. Why now

Same argument as the formatter in PR-002, only stronger: **retrofitting types is
miserable, and writing under them from line one costs nothing.**

But there is a second reason specific to you. You are learning Python semantics
while already knowing how to program. A type checker is the fastest available
teacher for exactly that gap — it will object to things that look obviously fine
to a JavaScript brain, and each objection is a lesson about how Python actually
behaves. §3.4 has two of those.

## 3. Commands run

### 3.1 Add it

```bash
uv add --dev mypy
```

Three transitive dependencies come with it — `mypy-extensions`, `pathspec`,
`typing-extensions`. Dev-only; none ship with your package.

### 3.2 Run it

```bash
uv run mypy
```

No arguments needed, because `files = ["src"]` in the config tells it what to
check. This is the same idea as `tsc` reading `tsconfig.json`.

### 3.3 The single most important thing to understand about mypy

**mypy's default mode is not "less strict". It is "mostly off".**

Here is a file that concatenates an integer and a string:

```python
def add(a, b):
    return a + b + "obviously wrong"


result: int = add(1, 2)
```

Default mypy:

```
Success: no issues found in 1 source file
```

Strict mypy, identical file:

```
lax.py:1: error: Function is missing a type annotation  [no-untyped-def]
lax.py:5: error: Call to untyped function "add" in typed context  [no-untyped-call]
Found 2 errors in 1 file (checked 1 source file)
```

**Why the default said nothing.** `add` has no annotations, so mypy treats it as
*dynamically typed* and **does not check its body at all**. Not "checks it
leniently" — skips it. Its return type becomes `Any`, and `Any` is compatible
with `int`, so the assignment passes too.

This is **not** how TypeScript behaves. With `strict: false`, `tsc` still checks
your code; it just infers `any` in more places and stops complaining about
`null`. mypy with defaults will silently ignore entire functions.

The reason is history, not design: mypy was built for **gradual typing** —
adding types to enormous untyped codebases one file at a time, which requires
unannotated code to pass. That is a real and valuable use case. It is not yours.
You are starting from zero, so you get to turn it all on now and never think
about it again.

**`Any` is contagious**, and this is why strict matters. One unannotated
function returns `Any`, which flows into its caller, which makes that
expression `Any`, which silences checks downstream. Strict mode's job is mostly
to stop `Any` entering the system in the first place.

### 3.4 Two things mypy catches that a JavaScript brain will not expect

#### `None` handling — familiar

```python
def find(symbol: str) -> str | None:
    return symbol if symbol else None


def shout(symbol: str) -> str:
    name = find(symbol)
    return name.upper()
```
```
opt.py:7: error: Item "None" of "str | None" has no attribute "upper"  [union-attr]
```

This one you already know — it is `strictNullChecks`. The fix is the same shape:
narrow before use, with `if name is None: ...` or `if name is not None: ...`.

#### `list` invariance — where Python is **stricter than TypeScript**

```python
def total(values: list[float]) -> float:
    return sum(values)


ints: list[int] = [1, 2, 3]
total(ints)
```
```
inv.py:6: error: Argument 1 to "total" has incompatible type "list[int]"; expected "list[float]"  [arg-type]
inv.py:6: note: "list" is invariant -- see https://mypy.readthedocs.io/en/stable/common_issues.html#variance
inv.py:6: note: Consider using "Sequence" instead, which is covariant
```

Every `int` *is* acceptable where a `float` is wanted. So why the rejection?

Because `list` is **mutable**. If `list[int]` were accepted as `list[float]`,
then `total` would be free to do `values.append(1.5)` — and the caller's
`ints: list[int]` would now contain a float. The type system would have lied.

So mypy makes mutable containers **invariant**: `list[int]` is not a `list[float]`,
full stop.

**TypeScript does not do this.** TS arrays are *covariant*, which is a
deliberate, documented unsoundness — `Dog[]` is assignable to `Animal[]`, and
pushing a `Cat` is accepted by the compiler and wrong at runtime. TS chose
convenience; Python chose soundness.

The fix is to say what you actually need. You only read the values, so ask for a
read-only type:

```python
from collections.abc import Sequence


def total(values: Sequence[float]) -> float:
    return sum(values)


ints: list[int] = [1, 2, 3]
total(ints)
```
```
Success: no issues found in 1 source file
```

`Sequence` is covariant because it has no `append`. **This is a design lesson
disguised as a type error**: accept the weakest interface that does the job, and
the variance works itself out. `Sequence` for "I will read it", `list` only for
"I will mutate it". You will apply this constantly from Phase 2 onward.

### 3.5 `reveal_type` — mypy's superpower

Drop `reveal_type(x)` anywhere and mypy prints what it thinks the type is at
that exact point:

```python
def parse(raw: str | None) -> None:
    reveal_type(raw)
    if raw is None:
        return
    reveal_type(raw)
    parts = raw.split(",")
    reveal_type(parts)
    reveal_type(parts[0].strip())
```
```
reveal.py:2: note: Revealed type is "str | None"
reveal.py:5: note: Revealed type is "str"
reveal.py:7: note: Revealed type is "list[str]"
reveal.py:8: note: Revealed type is "str"
```

**You can watch the narrowing happen.** Line 2 it is `str | None`; after the
early `return` it is `str`. That is *type narrowing*, and being able to print it
is how you debug a confusing type error instead of guessing.

TypeScript has no in-code equivalent — you hover in an editor. mypy makes it a
call you write, which means it works in any editor, in CI, and in a diff.

**Two things to know:**

1. **`reveal_type` does not exist at runtime.** It is a directive mypy
   understands; Python does not:
   ```
   NameError: name 'reveal_type' is not defined
   ```
   It is strictly a debugging tool. Remove it before committing.

2. **ruff has your back.** A forgotten `reveal_type` is an undefined name, so
   PR-002's `F` rules flag it. The two tools cover each other — which is the
   argument for running both rather than picking one.

   (Since 3.11 there is also `typing.reveal_type`, which *does* exist at runtime
   and prints at runtime. The bare, unimported form above is the one you want
   while debugging types.)

## 4. Packages introduced

| Package | What it is | Why this one | JS equivalent |
|---|---|---|---|
| **mypy** `2.3.1` | Static type checker | The original, the reference implementation, and the one whose behaviour the typing PEPs are written against. Best error messages for learning. | `tsc` |

## 5. The code, line by line

```toml
[tool.mypy]
python_version = "3.13"
files = ["src"]
strict = true
warn_unreachable = true
pretty = true
enable_error_code = [
    "ignore-without-code",  # bare `# type: ignore` is banned; name the code
    "redundant-expr",       # flags conditions that are always true/false
    "possibly-undefined",   # a name that may not be bound on every path
]
```

- **`python_version = "3.13"`** — which language version's semantics to assume.
  Affects which syntax is legal and which stdlib symbols exist. This is
  `tsconfig.json` → `target`, roughly.
- **`files = ["src"]`** — what to check when run with no arguments. PR-004 adds
  `"tests"` here. mypy errors if a listed path does not exist, which is why
  `tests` is not listed yet.
- **`strict = true`** — not one setting. It is a **bundle** that switches on
  about a dozen flags at once, the important ones being:

  | Flag | Effect |
  |---|---|
  | `disallow_untyped_defs` | Every function must be annotated |
  | `disallow_untyped_calls` | Typed code may not call untyped code |
  | `disallow_any_generics` | `list` alone is banned; write `list[int]` |
  | `warn_return_any` | Returning `Any` from a typed function is an error |
  | `warn_unused_ignores` | A `# type: ignore` that suppresses nothing is an error |
  | `strict_equality` | `1 == "1"` is flagged as a non-overlapping comparison |

  Enabling the bundle by name rather than the dozen flags individually means you
  automatically get new strictness as mypy adds it.

  One flag people expect here is **not** in the bundle because it is now on by
  default: `no_implicit_optional`. `def f(x: str = None)` is an error in any
  mode. Very old Python silently read that as `str | None`; PEP 484 prohibited
  it, and mypy changed its default accordingly.

- **`warn_unreachable = true`** — **not** part of `strict`, and worth having.
  Flags code the checker can prove never runs. This finds real bugs: a condition
  you thought could be true but cannot, given the types.
- **`pretty = true`** — render errors with source context and carets instead of
  bare `file:line: message`. Purely cosmetic, and worth it while learning.
- **`enable_error_code`** — opt-in checks beyond `strict`:
  - **`ignore-without-code`** — makes a bare `# type: ignore` an error; you must
    write `# type: ignore[arg-type]`. A bare ignore silences *every* error on
    that line forever, including future unrelated ones. This is the equivalent
    of banning bare `@ts-ignore` in favour of `@ts-expect-error`, and it is the
    single most valuable thing in this block.
  - **`redundant-expr`** — flags always-true / always-false conditions.
  - **`possibly-undefined`** — flags a name that may not be bound on every path
    (Python has no block scope, so a variable assigned only inside an `if` is
    still visible after it — see §6.3).

## 6. New syntax and concepts

### 6.1 `str | None` is a union type

```python
def find(symbol: str) -> str | None: ...
```

The `|` builds a union, exactly like TypeScript's `string | null`. The older
spelling is `Optional[str]` from `typing`, which you will see everywhere in
older code; they mean the same thing. Write `| None`. This project is 3.13.

### 6.2 Narrowing

mypy tracks control flow. After `if x is None: return`, the remaining code sees
`x` as `str`, not `str | None` — proven by §3.5's output. The narrowing
constructs are `is None` / `is not None`, `isinstance(x, T)`, truthiness checks,
and early `return` / `raise`. This is the same mental model as TypeScript's
narrowing, and it mostly transfers directly.

### 6.3 Python has no block scope

```python
if condition:
    total = 10
print(total)  # legal syntax; NameError if condition was False
```

There is no `let` and no block scoping. A name assigned inside `if`, `for` or
`while` is visible after it — bound if that branch ran, unbound if it did not.
Function scope is the only scope. `possibly-undefined` exists to catch exactly
this, and it is a genuine difference from JavaScript that will surprise you.

### 6.4 `Sequence` versus `list`

| Want | Annotate as | From |
|---|---|---|
| I will only read it | `Sequence[T]` | `collections.abc` |
| I will only iterate once | `Iterable[T]` | `collections.abc` |
| I will mutate it | `list[T]` | builtin |
| Key-value, read-only | `Mapping[K, V]` | `collections.abc` |
| Key-value, mutable | `dict[K, V]` | builtin |

Import these from **`collections.abc`**, not `typing` — the `typing` copies are
deprecated, the same history as `List` versus `list` in PR-002 §6.3.

## 7. Other ways this could have been written

| Option | Verdict |
|---|---|
| **`mypy`** | **Chosen.** Reference implementation; the typing PEPs are written against it. Clearest errors for learning, and its docs are the best explanation of Python's type system that exists. |
| `pyright` / Pylance | Much faster, better inference, powers VS Code's Python support. Written in TypeScript, Microsoft-maintained. A strong choice — and you may well end up running it in your editor *alongside* mypy in CI, which is a common and reasonable setup. |
| `pyre` | Meta's checker. Fast, but tuned for their codebase and thinner community. |
| `pytype` | Google's. Infers types for unannotated code, which is great for legacy work and unnecessary here. |
| Nothing | The actual default in most Python projects, and the reason "Python doesn't scale" is a widespread belief. It scales fine; unchecked code does not. |

**mypy and ruff do not overlap.** ruff reads one file at a time and matches
patterns. mypy builds a whole-program model and reasons about types across
module boundaries. ruff cannot know `find()` returns `str | None`; mypy cannot
tell you your imports are unsorted. Run both.

## 8. Exercises

1. **Watch strict earn its keep.** Recreate §3.3's `lax.py`, run
   `uv run mypy --no-incremental lax.py`, then add `--strict`. Then annotate
   `add(a: int, b: int) -> int` and run strict again — now it finally reports
   the actual bug in the body, which neither run caught before.

2. **Debug with `reveal_type`.** Add `reveal_type(__version__)` to
   `src/quantlab/__init__.py` and run `uv run mypy`. What does
   `importlib.metadata.version` claim to return? Remove it, and confirm
   `uv run ruff check .` would have caught you if you had not. (The answer is
   `Revealed type is "str"` — worth confirming rather than assuming, since
   `importlib.metadata` is exactly the kind of stdlib corner where a return type
   might surprise you.)

3. **Feel invariance.** Reproduce §3.4's `list[int]` error, then fix it with
   `Sequence`. Then try to `append` to the `Sequence` parameter and read the new
   error. That error *is* the explanation of why invariance exists.

4. **Meet implicit Optional.** Write `def f(x: str = None) -> None:` and run
   mypy *without* `--strict`. It still errors — `Incompatible default for
   parameter "x"` — and points at PEP 484. Very old Python read that signature
   as `str | None`; it no longer does. Now write it correctly, two ways: either
   `x: str | None = None`, or `x: str = ""`. Decide which one you actually
   meant. That decision is the lesson.

## 9. Merge checklist

- [x] `uv run mypy` — Success: no issues found in 2 source files
- [x] `uv run ruff check .` — All checks passed
- [x] `uv run ruff format --check .` — clean
- [x] `uv run python -m quantlab` prints `quantlab 0.1.0`
- [x] This document written
- [x] `docs/js-to-python.md` extended
- [x] `docs/prs/README.md` updated

## 10. What PR-004 will add

`pytest` — the first tests, the `tests/` layout, `conftest.py`, and why Python's
test discovery works the way it does. It also adds `"tests"` to mypy's `files`,
so your tests are type-checked too.
