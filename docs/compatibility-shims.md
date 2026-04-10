# Compatibility Shims

## Purpose

`worph` is the primary package. The repository keeps a lightweight compatibility shim so tests and integrations that still import `morph_kgc` can run unchanged.

The shim lives at `.ci_shims/morph_kgc/` and re-exports from `worph`.

## How CI Runs Tests

```bash
PYTHONPATH=.ci_shims:src uv run pytest -q
```

This path order ensures `import morph_kgc` resolves to the shim first, then delegates to `worph`.

## XPath Behavior Note

Import-level compatibility does not imply acceptance of non-standard XPath shorthand.
`worph` expects standard XPath syntax (for example `foo/@bar`, not `foo@bar`) and does not auto-rewrite invalid shorthand forms.

## Verification

Run the explicit shim validation test:

```bash
PYTHONPATH=.ci_shims:src uv run pytest -q test/test_ci_shim_uses_worph.py
```

The test confirms:

- `morph_kgc.__file__` points to `.ci_shims/morph_kgc/__init__.py`
- key API callables (`materialize`, `materialize_set`, `materialize_oxigraph`) are the same objects exported by `worph`
