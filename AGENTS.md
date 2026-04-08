# AGENTS.md

Repository-level instructions for agents working in `worph`.

## Scope and Precedence

- This file applies to the whole repository.
- These rules override higher-level defaults when they conflict.

## Required Context Discovery

Before proposing or implementing changes:

1. Read [README.md](README.md).
2. Read [CONTRIBUTING.md](CONTRIBUTING.md) if present.
3. Inspect [pyproject.toml](pyproject.toml) for dependencies and extras.
4. Inspect the relevant area under `src/worph/` and matching tests under `test/`.
5. If present and relevant, read `specs/lessons-learned.md`.

Do not change code before understanding the local module boundaries and nearby tests.

## Project Layout and Boundaries

- Python package code lives in `src/worph/`.
- Main entry points:
  - CLI: `src/worph/__main__.py`
  - Public API: `src/worph/__init__.py`
  - Materialization flow: `src/worph/materializer.py`
- Core submodules:
  - `core/`: configuration, mapping parsing, source loading, term maps, and emitters.
  - `fnml/`: FNML built-ins and execution.

Respect these boundaries. Keep orchestration in `materializer`, parsing/loading in `core`, and function execution logic in `fnml`.

## Build, Environment, and Dependency Rules

- Build backend: `hatchling` (configured in `pyproject.toml`).
- Preferred environment manager: `uv`.
- Install for development/testing:
  - `uv sync` when lock/config supports it, otherwise:
  - `uv pip install -e '.[test]'`
  - Fallback if `uv` is unavailable: `pip install -e '.[test]'`
- Do not add new dependencies unless the user explicitly approves.

## Testing and Verification

- Test framework: `pytest`.
- Start with smallest relevant scope:
  - Single test file or directory under `test/...`
  - Expand only if required by impact.
- Typical commands:
  - `uv run pytest test/<area>/<case>/test_*.py`
  - `uv run pytest test/issues/issue_<n>`
  - `PYTHONPATH=.ci_shims:src uv run pytest -q` (compat mode/full suite)
  - `uv run pytest` (full suite, non-shim mode)
- For behavior changes, update/add tests in the closest existing test area.
- Do not claim completion without reporting what tests were run and their results.

## Change Discipline

- Keep patches minimal and focused; avoid unrelated refactors.
- Preserve existing coding style and naming in touched files.
- Reuse existing helpers/utilities before introducing new abstractions.
- Avoid architecture changes unless explicitly requested.
- Do not modify unrelated files.
- In specs/docs, use relative paths only. Do not use absolute paths.

## Repository Subagents (`specs/agents`)

- Use only the minimum specialist set needed for the task.
- Keep the loaded agent set small (max 3 specialists for most tasks).
- Default specialist pair when uncertain: `python-expert` + `reviewer`.
- Available specialist briefs live in `specs/agents/`:
  - `python-expert.md`
  - `oop-gof-expert.md`
  - `yarrrml-rml-rdf-xpath-expert.md`
  - `gh-expert.md`
  - `reviewer.md`

## Safety and Git Rules

- Never use destructive git commands (for example `git reset --hard`) unless explicitly requested.
- Do not push, open PRs, or rewrite history unless explicitly instructed.
- If unexpected repository changes appear while working, stop and ask how to proceed.

## Communication Expectations

At task completion, report:

1. What was changed.
2. Which files were modified.
3. Which tests were run and outcomes.
4. Any residual risks or follow-up work.
