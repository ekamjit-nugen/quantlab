# quantlab

A market-research and backtesting toolkit, built in small teaching PRs as a
structured way to learn Python.

Every PR ships code, tests, and a document in [`docs/prs/`](docs/prs/) that
explains what was added, which packages were used and why, what each line does,
what new syntax appeared, and what the JavaScript equivalent would be.

- **[Roadmap](docs/roadmap.md)** — 13 phases, ~65 PRs, ~6 months
- **[PR index](docs/prs/README.md)** — every PR and what it teaches
- **[JS to Python](docs/js-to-python.md)** — the Rosetta stone

## Quickstart

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv sync
```

```bash
uv run python -m quantlab
```

```
quantlab 0.1.0
```

## Requirements

Python 3.13 (uv installs and pins it for you).
