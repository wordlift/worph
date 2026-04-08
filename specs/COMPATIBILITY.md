# Compatibility Contract (V2)

## Scope
V2 must preserve user-visible behavior for supported YARRRML/RML/FNML scenarios covered by retained regression tests under `test/`.

## Initial Guarantees
- Primary package name is `worph`.
- Legacy import compatibility for `morph_kgc` is provided in CI through `.ci_shims/morph_kgc`.
- Public entry points reserved:
  - `materialize`
  - `materialize_oxigraph`
  - `materialize_set`
  - `materialize_kafka`
  - `translate_to_rml`
- Primary CLI command is `worph`.

## Performance Targets
- Establish baseline from legacy branch and require measurable improvements before release.

## Validation Gate
- No release until conformance + performance test gates are green.
