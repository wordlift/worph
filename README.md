# worph

[![CI](https://github.com/wordlift/worph/actions/workflows/ci.yml/badge.svg)](https://github.com/wordlift/worph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/worph.svg)](https://pypi.org/project/worph/)
[![Python versions](https://img.shields.io/pypi/pyversions/worph.svg)](https://pypi.org/project/worph/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

![worph logo](assets/worph-logo.png)

`worph` is a public GitHub project at [`wordlift/worph`](https://github.com/wordlift/worph), forked from [`morph-kgc`](https://github.com/morph-kgc/morph-kgc), with a focus on a clean next-generation rewrite.

## Current Scope

- Keep regression coverage and planning assets (`test/`, `specs/`, `AGENTS.md`, `docs/`)
- Build and evolve the primary implementation under `src/worph/`
- Preserve legacy import compatibility in CI via `.ci_shims/morph_kgc -> worph`

## Compatibility in CI

Some retained tests still import `morph_kgc`. CI runs with:

```bash
PYTHONPATH=.ci_shims:src uv run pytest -q
```

This keeps `worph` as the real implementation while allowing `import morph_kgc` for compatibility checks.

## Publish to PyPI

Publishing is handled by GitHub Actions with OIDC Trusted Publishing:

- Workflow: `.github/workflows/ci.yml` (`publish` job, gated by `test-and-examples`)
- Trigger: push a version tag like `0.1.2` or `v0.1.2`

One-time setup on `pypi.org`:

1. Create project `worph` (or use existing one).
2. Add a Trusted Publisher with:
   - Owner: `wordlift`
   - Repository: `worph`
   - Workflow name: `ci.yml`
   - Environment: leave empty (unless you add one in GitHub Actions)

## License

All code and documentation in this repository are licensed under the Apache License 2.0.
