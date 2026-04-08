from __future__ import annotations

from collections import OrderedDict

from worph.core.model import LogicalSource, MappingDocument, TermMap, TriplesMap
from worph.core.sources import Record
from worph.materializer import _RenderContext, _quoted_terms_from_map


def _tm(identifier: str, source: str) -> TriplesMap:
    return TriplesMap(
        identifier=identifier,
        logical_source=LogicalSource(source=source, reference_formulation="csv"),
        subject_map=TermMap(template=f"http://example.com/{identifier}/{{id}}"),
        class_iris=["http://example.com/Class"],
    )


def test_cross_source_quoted_cache_is_bounded_and_lru(monkeypatch) -> None:
    monkeypatch.setattr("worph.materializer._CROSS_SOURCE_QUOTED_CACHE_MAX", 2)
    current = _tm("current", "current.csv")
    ref1 = _tm("ref1", "ref1.csv")
    ref2 = _tm("ref2", "ref2.csv")
    ref3 = _tm("ref3", "ref3.csv")
    mapping = MappingDocument(prefixes={}, base=None, triples_maps=[current, ref1, ref2, ref3])
    tm_by_id = {tm.identifier: tm for tm in mapping.triples_maps}
    rows = [Record(values={"id": "1"})]
    context = _RenderContext(
        mapping=mapping,
        rows_by_tm={key: rows for key in tm_by_id},
        tm_by_id=tm_by_id,
        subject_cache={},
        triples_cache={},
        in_progress=set(),
        join_index_cache={},
        cross_source_quoted_cache=OrderedDict(),
    )

    _quoted_terms_from_map(context, "ref1", "current", 0)
    _quoted_terms_from_map(context, "ref2", "current", 0)
    _quoted_terms_from_map(context, "ref1", "current", 0)  # refresh LRU order
    _quoted_terms_from_map(context, "ref3", "current", 0)  # should evict ref2

    assert list(context.cross_source_quoted_cache.keys()) == ["ref1", "ref3"]
