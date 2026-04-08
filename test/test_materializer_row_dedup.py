from __future__ import annotations

from worph.core.model import LogicalSource, MappingDocument, TermMap, TriplesMap
from worph.materializer import _collect_rows


def test_collect_rows_reuses_rows_for_equivalent_logical_sources(monkeypatch) -> None:
    shared_source = LogicalSource(
        source="data.csv",
        reference_formulation="csv",
        iterator=None,
        query=None,
        namespaces=None,
    )
    mapping = MappingDocument(
        prefixes={},
        base=None,
        triples_maps=[
            TriplesMap(identifier="tm1", logical_source=shared_source, subject_map=TermMap(template="http://ex/{id}")),
            TriplesMap(identifier="tm2", logical_source=shared_source, subject_map=TermMap(template="http://ex/{id}")),
        ],
    )
    calls = {"count": 0}

    def _fake_iter_records(**kwargs):
        calls["count"] += 1
        yield {"id": "1"}

    monkeypatch.setattr("worph.materializer.iter_records", _fake_iter_records)

    rows_by_tm = _collect_rows(mapping)

    assert calls["count"] == 1
    assert rows_by_tm["tm1"] is rows_by_tm["tm2"]


def test_collect_rows_reuses_rows_for_equivalent_sources_with_reordered_namespaces(monkeypatch) -> None:
    source_a = LogicalSource(
        source="data.csv",
        reference_formulation="csv",
        namespaces={"b": "2", "a": "1"},
    )
    source_b = LogicalSource(
        source="data.csv",
        reference_formulation="csv",
        namespaces={"a": "1", "b": "2"},
    )
    mapping = MappingDocument(
        prefixes={},
        base=None,
        triples_maps=[
            TriplesMap(identifier="tm1", logical_source=source_a, subject_map=TermMap(template="http://ex/{id}")),
            TriplesMap(identifier="tm2", logical_source=source_b, subject_map=TermMap(template="http://ex/{id}")),
        ],
    )
    calls = {"count": 0}

    def _fake_iter_records(**kwargs):
        calls["count"] += 1
        yield {"id": "1"}

    monkeypatch.setattr("worph.materializer.iter_records", _fake_iter_records)

    rows_by_tm = _collect_rows(mapping)

    assert calls["count"] == 1
    assert rows_by_tm["tm1"] is rows_by_tm["tm2"]
