# Reimplementation Scope Matrix

This matrix defines the mandatory behavior for the worph from-scratch runtime.

## Feature Scope

| Area | Required Capability | Primary Test Areas |
|---|---|---|
| Configuration/runtime | Parse INI config deterministically; resolve relative mapping/source paths from config location | `test/*` (all suites), examples |
| RML/R2RML parsing | Parse triples maps, logical sources/tables, subject/predicate/object maps, joins | `test/rml-core`, `test/r2rml`, `test/rml-tv` |
| YARRRML parsing | Parse `prefixes`, `sources`, `mappings`, PO shortcuts, function specs, `~iri` and source hints (e.g. `~shapefile`) | `test/issues/issue_254`, `test/shapefile`, `test/rml-fnml` |
| Source loading | CSV/TSV/JSON/XML/SQLite/tabular/geospatial sources and in-memory sources | `test/rml-core`, `test/rml-in-memory`, `test/geoparquet`, `test/shapefile` |
| Reference extraction | CSV field refs, JSONPath, XPath (standard syntax; no shorthand auto-rewrite), SQL row refs | `test/rml-core`, `test/rml-tv` |
| Term rendering | constant/template/reference/function precedence and node rendering by role/type | `test/rml-core`, `test/issues`, `test/r2rml` |
| Join semantics | parent triples map joins with conditions and deterministic parent matching | `test/rml-core`, `test/rml-tv` |
| FNML execution | nested function calls, parameter mapping, condition gating | `test/rml-fnml`, `test/issues/issue_254` |
| RDF-star semantics | quoted triples maps and asserted/non-asserted handling | `test/rml-star`, `test/issues/issue_124`, `test/issues/issue_174` |
| Datatype coercion | SQL datatype lexical normalization and typed literal generation | `test/r2rml`, `test/issues/issue_67` |
| Public API compatibility | `materialize`, `materialize_set`, `materialize_oxigraph`, CLI paths | broad suite + examples |
| CI compatibility shim | `morph_kgc` shim imports resolve to worph behavior | `test/test_ci_shim_uses_worph.py` |

## Out of Scope (for initial DoD)

- Runtime fallback to upstream `morph_kgc` execution code.
- New user-facing features not covered by current suite/specs.

## Definition of Done Alignment

- Full compatibility suite passes with `PYTHONPATH=.ci_shims:src uv run pytest -q`.
- No runtime execution path delegates to upstream `morph_kgc`.
