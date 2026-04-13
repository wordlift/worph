# Publish Workflow Spec

## Goal
Publish a patch release with a deterministic loop:

1. bump patch
2. refresh dependencies and lock
3. commit
4. tag
5. push branch and tags
6. monitor GitHub workflow
7. if workflow fails, fix issues and restart from step 1

## Preconditions

1. Run from repository root on the intended release branch (normally `main`).
2. Working tree must be clean before starting a release cycle.
3. `gh` CLI must be authenticated.
4. `uv` must be available.

## Release Cycle

1. Bump patch version in `pyproject.toml`.
2. Refresh lock/deps:
   - `uv lock --upgrade`
   - If needed: `uv sync --extra test`
3. Run validation before commit:
   - Minimum: targeted tests for changed areas
   - Required gate: `PYTHONPATH=.ci_shims:src uv run pytest -q`
4. Commit release changes:
   - `git add ...`
   - `git commit -m "release: vX.Y.Z"`
5. Create/update tag:
   - `git tag vX.Y.Z`
6. Push branch and tag:
   - `git push origin <branch>`
   - `git push origin --tags`

## Monitoring

1. Find runs for the pushed commit/tag:
   - `gh run list --limit 20`
2. Wait/poll until all relevant runs finish:
   - `gh run watch <run-id>` (or poll with `gh run list`)
3. Success condition:
   - All required CI workflows for the release commit complete with `success`.

## Failure Handling

If any required workflow fails:

1. Inspect failure details/logs:
   - `gh run view <run-id> --log-failed`
2. Fix root cause in repository code/workflow/config.
3. Validate locally again:
   - `PYTHONPATH=.ci_shims:src uv run pytest -q`
4. Restart **entire release cycle** from patch bump:
   - bump to next patch version (`X.Y.(Z+1)`)
   - refresh lock
   - commit
   - tag
   - push
   - monitor

Do not reuse the failed tag/version.

## Exit Criteria

The workflow is complete only when:

1. release commit is pushed
2. release tag is pushed
3. required GitHub workflows for that release commit are all green

## Current Release Example

- Patch target example: `v0.1.11`
