# PR index

Every PR in this repository ships code, tests, and a teaching document. The
document is the real deliverable — the code is almost a side effect.

## How each document is structured

1. **What this PR adds** — summary and file list
2. **Why now** — what it unblocks
3. **Commands run** — every command, flag by flag
4. **Packages introduced** — what, why this one, JS equivalent
5. **The code, line by line**
6. **New syntax** — each construct, with the JS analogue
7. **Other ways this could have been written** — alternatives, and why not
8. **Exercises** — small changes to make yourself
9. **Merge checklist**

## Rules

| Rule | Value |
|---|---|
| Size | <= 300 changed lines, ideally ~100 |
| Scope | **One** new concept. Explaining two things means two PRs. |
| State | `main` is always green: lint + types + tests pass |
| Doc | No PR merges without its teaching document |
| Time | 1-3 hours |

## Merged

| PR | Title | Concepts | Packages |
|---|---|---|---|
| [001](PR-001-scaffold.md) | Project scaffold, `src` layout, `python -m` | packages, `__init__.py`, `__main__.py`, docstrings, f-strings, the `__name__` guard, virtual environments, dunders + name mangling, runtime-preserved annotations | `uv`, `uv_build` |

## Planned — Phase 0, Foundations

| PR | Title |
|---|---|
| 002 | `ruff` — linting and formatting, plus the single-source version fix (pulled forward from 020) |
| 003 | `mypy --strict` — the type checker |
| 004 | `pytest` — first test, layout, `conftest.py` |
| 005 | `pre-commit` hooks |
| 006 | GitHub Actions CI |
| 007 | `core/config.py` — dataclasses, env vars, `pathlib` |

## Planned — Phase 1, The data model

| PR | Title |
|---|---|
| 008 | `Money` — why `Decimal`, never `float` |
| 009 | `Symbol` and `Side` — `Enum`, `Literal`, `StrEnum` |
| 010 | `Bar` and `Tick` — frozen slotted dataclasses |
| 011 | Timestamps — `datetime`, `zoneinfo`, UTC discipline |
| 012 | `Order` and `Position` — generics, `TypeVar`, `Self` |
| 013 | Equality, hashing, `__repr__` — the data-model dunders |

## Planned — Phase 2, Collections, laziness, first DSA

| PR | Title |
|---|---|
| 014 | CSV bar loader — the `csv` module, `with`, file handling |
| 015 | Generators — streaming bars lazily |
| 016 | `itertools` and `functools` in anger |
| 017 | Ring buffer with `deque` — your first data structure |
| 018 | Naive rolling SMA — O(n*w), and measuring it |
| 019 | Incremental rolling SMA/stdev — O(1)/bar, benchmarked against 018 |
| 020 | `[project.scripts]` — a real `quantlab` command |

Later phases are listed in [`../roadmap.md`](../roadmap.md). Their individual
PRs get planned when the phase starts — mapping out 65 PRs six months ahead
would be fake precision.
