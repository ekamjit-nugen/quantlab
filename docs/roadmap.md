# Roadmap

`quantlab` is a market-research and backtesting toolkit that exists to teach
Python properly — the language, its idioms, its data structures, its concurrency
story, its ecosystem, and finally agentic AI on top.

Pace: ~5-7 hrs/week, 2-3 PRs/week, ~65 PRs, ~6 months.

## Architecture

A modular monolith with `Protocol`-based seams. Every subsystem is defined by a
`typing.Protocol`; implementations register themselves through `pyproject.toml`
entry points.

```
src/quantlab/
  core/        zero deps: types, protocols, registry, errors, config, clock
  ds/          data structures implemented here, used for real
  data/        BarSource impls: csv, yfinance, ccxt, mt5-bridge, duckdb
  indicators/  pure functions over series
  backtest/    event-driven engine + metrics
  strategy/    Strategy protocol + registry
  risk/        position sizing
  store/       Repository protocol: sqlite -> duckdb -> postgres
  agents/      LLM layer, tools, loops, RAG   (phases 10-12)
  cli/         typer
  api/         fastapi + websockets
```

The five seams: `BarSource`, `Strategy`, `Repository`, `LLMClient`, `Tool`.

**Adding a new tech stack = one class satisfying one Protocol, plus one line in
`pyproject.toml`. Core never changes.**

## Tooling decisions

| Concern | Choice | Why |
|---|---|---|
| Python | 3.13, pinned | 3.14 is too new for parts of the Phase 7 data stack |
| Env + deps | `uv` | One tool for versions, venvs, deps, running |
| Lint + format | `ruff` | Replaces black + isort + flake8 + pyupgrade |
| Types | `mypy --strict` from day one | The single biggest accelerator for a TypeScript developer |
| Tests | `pytest` + `hypothesis` | Property tests fit indicators unusually well |

## Phases

**0 — Foundations** (1.5 wks) — tooling, `src` layout, ruff, mypy, pytest,
pre-commit, CI, config.

**1 — The data model** (2 wks) — dataclasses, `Enum`, `Protocol`, generics,
`Decimal` for money, `zoneinfo` for time, the data-model dunders.

**2 — Collections, laziness, first DSA** (2 wks) — `collections`, `itertools`,
`functools`, generators. Ring buffer; naive O(n*w) rolling stats vs incremental
O(1)/bar, benchmarked against each other. No pandas yet — the point is Python.

**3 — OOP and the plugin spine** (2 wks) — classes, `Protocol` vs `ABC`,
decorators, context managers, the registry, entry-point discovery.

**4 — Errors, logging, rigor** (2 wks) — exception hierarchies, `raise from`,
EAFP, `logging`, pytest depth, `hypothesis`, coverage gates.

**5 — Backtester + heavy DSA** (3 wks) — event loop; `heapq` then a hand-rolled
binary heap; `bisect` and a skip list for price levels; trie for symbol search;
graph + topological sort for indicator dependencies; union-find for correlation
groups; sliding-window drawdown; DP optimal-trade. Complexity annotated in
docstrings and proven with `pytest-benchmark`.

**6 — Concurrency** (2 wks) — the GIL, and when threads vs processes vs async
each actually win. `concurrent.futures`, `multiprocessing` parameter sweep
(CPU-bound), `asyncio` + `httpx` multi-symbol fetch (IO-bound). Having both in
one codebase is what makes the distinction stick.

**7 — Data stack** (2 wks) — `sqlite3` and DB-API, `Repository` protocol,
SQLAlchemy 2.0 typed, Alembic, DuckDB + Parquet, numpy vectorisation, polars.
Rewrite the Phase 2 indicators vectorised and benchmark: that before/after
number is the most instructive thing in the plan.

**8 — Interfaces** (2 wks) — `typer` + `rich` CLI, FastAPI + Pydantic v2,
dependency injection, WebSocket quote streaming.

**9 — Packaging and speed** (2 wks) — wheels, versioning, Docker, CI matrix,
`cProfile` / `py-spy` / `memray`, then the hot loop rewritten in Rust via PyO3.

**10 — LLM fundamentals** (2 wks) — Anthropic SDK, streaming, structured output
via tools, token counting, prompt caching, cost tracking, `LLMClient` protocol.

**11 — The agent loop, hand-written** (2 wks) — write the loop yourself; do not
start with a framework. Tool schemas generated from your own function signatures
via `inspect` + type hints, which pays Phase 1 back directly. State, error
recovery, turn budgets, guardrails.

**12 — RAG, memory, multi-agent, MCP** (3 wks) — implement cosine vector search
over numpy yourself, then simplified HNSW, before touching a vector DB. Chunking,
hybrid retrieval, reranking, agent memory, a supervisor over researcher /
backtester / risk-reviewer agents, an MCP server, an eval harness.

## Three parallel habits

1. **Pythonic refactor Friday** — 30 min revisiting Phase N-3 code. Your Phase 2
   code will look wrong by Phase 5, and noticing that *is* the learning.
2. **`docs/complexity.md`** — every structure implemented, with measured
   numbers, not just Big-O.
3. **One stdlib module per week** — `pathlib`, `datetime`, `re`, `json`, `csv`,
   `subprocess`, `inspect`, `typing`, `abc`, `weakref`, `array`. 20 min each.

## Two traps this domain will set

- **Floats for money.** Handled in PR-008 by making `Money` wrap `Decimal`.
- **Naive datetimes.** Everything UTC internally via `zoneinfo`, converted only
  at display. Market data punishes anything else, and it punishes silently.
