from __future__ import annotations

from collections import OrderedDict

from rdflib import Literal
from rdflib.namespace import XSD

from worph.core.model import LogicalSource, MappingDocument, ObjectMapSpec, TermMap, TriplesMap
from worph.core.sources import Record
from worph.materializer import _RenderContext, _render_tm_row_object_terms


def _build_context_with_language_map() -> tuple[_RenderContext, ObjectMapSpec]:
    tm = TriplesMap(
        identifier="tm1",
        logical_source=LogicalSource(source="s.csv", reference_formulation="csv"),
        subject_map=TermMap(template="http://example.com/s/{id}", term_type="iri"),
        po_maps=[],
    )
    mapping = MappingDocument(prefixes={}, base=None, triples_maps=[tm])
    context = _RenderContext(
        mapping=mapping,
        rows_by_tm={"tm1": [Record(values={"id": "1", "name": "alpha"})]},
        tm_by_id={"tm1": tm},
        subject_cache={},
        triples_cache={},
        in_progress=set(),
        join_index_cache={},
        cross_source_quoted_cache=OrderedDict(),
    )
    object_map = ObjectMapSpec(
        term_map=TermMap(
            reference="name",
            term_type="literal",
            datatype=str(XSD.string),
            language="fr",
            language_map=TermMap(reference="lang"),
        )
    )
    return context, object_map


def test_language_map_list_uses_first_value(monkeypatch) -> None:
    context, object_map = _build_context_with_language_map()

    def _fake_render_term_map(term_map, record, formulation, namespaces=None):
        if term_map.reference == "lang":
            return ["en", "de"]
        if term_map.reference == "name":
            return "alpha"
        raise AssertionError("unexpected term map")

    monkeypatch.setattr("worph.materializer.render_term_map", _fake_render_term_map)
    terms = _render_tm_row_object_terms(context, object_map, "tm1", 0)
    node = terms[0]
    assert isinstance(node, Literal)
    assert node.language == "en"
    assert node.datatype is None


def test_language_map_empty_list_removes_language(monkeypatch) -> None:
    context, object_map = _build_context_with_language_map()

    def _fake_render_term_map(term_map, record, formulation, namespaces=None):
        if term_map.reference == "lang":
            return []
        if term_map.reference == "name":
            return "alpha"
        raise AssertionError("unexpected term map")

    monkeypatch.setattr("worph.materializer.render_term_map", _fake_render_term_map)
    terms = _render_tm_row_object_terms(context, object_map, "tm1", 0)
    node = terms[0]
    assert isinstance(node, Literal)
    assert node.language is None
    assert node.datatype is None


def test_language_map_scalar_value_is_applied(monkeypatch) -> None:
    context, object_map = _build_context_with_language_map()

    def _fake_render_term_map(term_map, record, formulation, namespaces=None):
        if term_map.reference == "lang":
            return "it"
        if term_map.reference == "name":
            return "alpha"
        raise AssertionError("unexpected term map")

    monkeypatch.setattr("worph.materializer.render_term_map", _fake_render_term_map)
    terms = _render_tm_row_object_terms(context, object_map, "tm1", 0)
    node = terms[0]
    assert isinstance(node, Literal)
    assert node.language == "it"
    assert node.datatype is None


def test_language_map_none_keeps_static_language_fallback(monkeypatch) -> None:
    context, object_map = _build_context_with_language_map()

    def _fake_render_term_map(term_map, record, formulation, namespaces=None):
        if term_map.reference == "lang":
            return None
        if term_map.reference == "name":
            return "alpha"
        raise AssertionError("unexpected term map")

    monkeypatch.setattr("worph.materializer.render_term_map", _fake_render_term_map)
    terms = _render_tm_row_object_terms(context, object_map, "tm1", 0)
    node = terms[0]
    assert isinstance(node, Literal)
    assert node.language == "fr"
    assert node.datatype is None
