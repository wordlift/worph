# TODO - worph Full Reimplementation (No morph_kgc Runtime Dependency)

## Rules
- Do not rely on upstream `morph_kgc` runtime code paths.
- Keep compatibility API surface, but all behavior must be provided by `worph`.
- Validate each step before moving to the next.

## Phase 0 - Scope Freeze
- [x] Build feature scope matrix from existing tests and docs.
- [x] Categorize current failures by area (parser/source/FNML/RDF-star/R2RML/etc.).
- [x] Record baseline command and baseline counts.

## Phase 1 - Foundations
- [x] Finalize architecture boundaries (`domain`, `parsing`, `source`, `function`, `execution`, `output`, `api`).
- [x] Keep runtime configuration/path resolution deterministic.
- [x] Ensure error model is explicit and deterministic (no silent fallbacks).

## Phase 2 - Source/Parsing Parity
- [x] YARRRML source normalization parity (including `~shapefile`).
- [x] SQL query logical source handling parity for RMLTV fixtures.
- [x] Geospatial/parquet/shapefile source record normalization parity.

## Phase 3 - Semantic Engine Parity
- [x] Term map rendering parity (constant/template/reference/function precedence).
- [x] Join behavior parity (`parentTriplesMap`, join conditions).
- [x] FNML/function execution parity including nested calls.

## Phase 4 - RDF-star + Typed Literals
- [x] Implement quoted triple semantics (`rml:quotedTriplesMap`).
- [x] Implement asserted/non-asserted triples-map behavior.
- [x] Fix SQL datatype coercion parity for R2RML tests.

## Phase 5 - CI/Release Readiness
- [x] Full CI-equivalent test suite green in shim mode.
- [x] Example matrix green.
- [x] Docs/specs updated with final architecture and guarantees.

## Phase 6 - YARRRML/RML Spec Coverage Expansion
- [x] Add contract test for YARRRML multi-source behavior.
- [x] Add contract test for named-graph + non-asserted handling.
- [x] Add contract test for quoted triples behavior across `materialize` vs `materialize_set`.
- [x] Add contract test for unknown FNML function behavior.
- [x] Add YARRRML condition syntax matrix test (`po`/`predicateobjects`/`predicateObjects`).
- [x] Add public API contract tests (`translate_to_rml`, `materialize_kafka`).
- [x] Extend YARRRML multi-source tests with ordering and invalid-source paths.
- [x] Extend condition tests with false branch and unknown-condition function path.
- [x] Strengthen API contracts with deterministic assertions/messages.
- [x] Add deeper quoted-triple parity assertions across set/oxigraph modes.
- [x] Re-run full suite and confirm green.
- [x] Re-run YARRRML/RML expert review and close gaps.

## Phase 7 - Code Quality Remediation (Review-Driven)
- [x] FNML built-in registry cleanup:
  - Remove duplicate `fun_id` registrations.
  - Eliminate duplicate/misleading Python function names.
  - Add guardrails/tests for registry integrity.
- [x] FNML evaluator state cleanup:
  - Remove hidden mutable module-global evaluator coupling.
  - Keep UDF configuration behavior deterministic and testable.
- [x] Materializer maintainability and performance:
  - Add logical-source equivalence behavior to domain model.
  - Refactor hot paths into smaller helpers.
  - Optimize join evaluation with indexed lookups.
  - Cache cross-source quoted triples reuse.
  - Reduce repeated row-materialization for equivalent logical sources.
- [x] Term-map rendering performance:
  - Replace recursive template expansion with iterative/tokenized expansion.
- [x] Parser maintainability:
  - Extract duplicated FNML parameter parsing logic.
  - Introduce loader parser strategy map instead of hardcoded branching.
- [x] Test hardening for review findings:
  - Path precedence conflict tests (CWD vs config-relative).
  - Dataframe graph-correctness assertions (not just no-crash).
  - XPath fallback/error branch tests.
  - CSV-query formatting variant tests.
  - Condition truthiness matrix + recursion guard tests.
- [ ] Full regression run:
- [x] Full regression run:
  - `PYTHONPATH=.ci_shims:src uv run pytest -q`
- [x] Team re-review after fixes and iterate until no critical findings remain.

## Coverage Notes
- [x] Coverage reporting enabled in CI (`pytest-cov` + `--cov=src/worph --cov-report=term`).
- [ ] Repository-wide 90% coverage threshold (current full-suite baseline is ~59%; requires a dedicated coverage expansion effort).

## Definition of Done
- [x] `PYTHONPATH=.ci_shims:src uv run pytest -q` passes.
- [x] No runtime dependency on upstream `morph_kgc` execution paths.
- [ ] Required CI jobs pass consistently.
- [x] README/docs/specs reflect final behavior.
