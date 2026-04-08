from __future__ import annotations

from rdflib import URIRef

from worph.core.model import JoinCondition, LogicalSource, MappingDocument, ObjectMapSpec, PredicateObjectMap, TermMap, TriplesMap
from worph.core.sources import Record
from worph.materializer import materialize_set_from_mapping


def _build_join_mapping() -> MappingDocument:
    parent_tm = TriplesMap(
        identifier="parent",
        logical_source=LogicalSource(source="parent.csv", reference_formulation="csv"),
        subject_map=TermMap(template="http://example.com/parent/{id}"),
    )
    child_tm = TriplesMap(
        identifier="child",
        logical_source=LogicalSource(source="child.csv", reference_formulation="csv"),
        subject_map=TermMap(template="http://example.com/child/{id}"),
        po_maps=[
            PredicateObjectMap(
                predicate_maps=[TermMap(constant=str(URIRef("http://example.com/p")), term_type="iri")],
                object_maps=[
                    ObjectMapSpec(
                        parent_triples_map="parent",
                        join_conditions=[JoinCondition(child="k", parent="k")],
                    )
                ],
            )
        ],
    )
    return MappingDocument(prefixes={}, base=None, triples_maps=[parent_tm, child_tm])


def test_join_index_handles_mixed_key_type_dict_values(monkeypatch) -> None:
    mapping = _build_join_mapping()

    def _fake_iter_records(**kwargs):
        source = kwargs["source"]
        if source == "parent.csv":
            yield Record(values={"id": "p1", "k": {"1": "a", 1: "a"}})
        else:
            # Same logical dict content, different insertion order.
            yield Record(values={"id": "c1", "k": {1: "a", "1": "a"}})

    monkeypatch.setattr("worph.materializer.iter_records", _fake_iter_records)

    triples = materialize_set_from_mapping(mapping)

    assert any("http://example.com/child/c1" in t and "http://example.com/parent/p1" in t for t in triples)


def test_join_index_list_values_remain_order_sensitive(monkeypatch) -> None:
    mapping = _build_join_mapping()

    def _fake_iter_records(**kwargs):
        source = kwargs["source"]
        if source == "parent.csv":
            yield Record(values={"id": "p1", "k": ["x", "y"]})
        else:
            yield Record(values={"id": "c1", "k": ["x", "y"]})
            yield Record(values={"id": "c2", "k": ["y", "x"]})

    monkeypatch.setattr("worph.materializer.iter_records", _fake_iter_records)

    triples = materialize_set_from_mapping(mapping)

    assert any("http://example.com/child/c1" in t and "http://example.com/parent/p1" in t for t in triples)
    assert not any("http://example.com/child/c2" in t and "http://example.com/parent/p1" in t for t in triples)
