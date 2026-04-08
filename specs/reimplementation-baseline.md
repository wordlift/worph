# Reimplementation Baseline (Phase 0)

## Baseline Command

```bash
PYTHONPATH=.ci_shims:src uv run pytest -q
```

## Baseline Result

- Failed: `46`
- Passed: `326`
- Skipped: `1`
- Source log: `/tmp/worph-baseline-pytest.log`

## Failure Clusters

1. RDF-star semantics/parsing and quoted triples
- `test/rml-star/*` (16 failures)
- `test/issues/issue_124`
- `test/issues/issue_174` (3 failures)

2. R2RML SQL datatype/parity issues
- `test/r2rml/*` (17 failures)
- related typed literal mismatch in `test/issues/issue_67`

3. Source/parsing gaps
- Shapefile source interpreted as CSV: `test/shapefile/RMLTC0001a`
- Geoparquet geometry bytes not converted to WKT: `test/geoparquet/RMLTC0001a`
- RMLTV SQL-over-CSV query handling: `test/rml-tv/RMLTVTC0026a`, `test/rml-tv/RMLTVTC0027a`

4. Additional issue regressions
- `test/issues/issue_145`
- `test/issues/issue_81`
- `test/issues/issue_254`

## Prioritized Fix Order

1. Source/parsing gaps (`shapefile`, `geoparquet`, `rml-tv query parser`)
2. RDF-star quoted triples semantics
3. R2RML SQL datatype normalization/coercion parity
4. Remaining issue-specific regressions and full-suite stabilization
