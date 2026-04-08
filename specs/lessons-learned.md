# Lessons Learned

## 2026-04-07

- Context: Defining repository documentation conventions for specs/docs.
- Lesson: Use relative paths in specs and docs; avoid absolute paths.
- Prevention/Practice: When writing or updating specs/docs, verify links and file paths are repository-relative before finalizing.

- Context: Aligning `AGENTS.md` with documentation path policy and repository subagent workflow.
- Lesson: Repository guidance should explicitly reference `specs/agents` and keep the specialist set minimal.
- Prevention/Practice: When editing process docs, verify agent paths and specialist names exist in `specs/agents` before finalizing.

## 2026-04-08

- Context: CI needed to run retained tests that still import `morph_kgc` after moving primary implementation to `worph`.
- Lesson: Shim path order matters; run compatibility mode with `PYTHONPATH=.ci_shims:src` so `morph_kgc` resolves to shim modules first.
- Prevention/Practice: Keep one explicit shim verification test (`test/test_ci_shim_uses_worph.py`) and document the exact command in README/docs.
