from __future__ import annotations

import worph as morph_kgc
from rdflib import Literal, URIRef
from rdflib.namespace import XSD


def _materialize_from_mapping(tmp_path, mapping_body: str):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id\n1\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.ttl"
    mapping_path.write_text(mapping_body, encoding="utf-8")
    config = f"[DataSource]\nmappings={mapping_path.as_posix()}"
    return morph_kgc.materialize(config)


def _objects_for_predicate(graph, predicate_iri: str):
    return [object_ for _, predicate, object_ in graph if str(predicate) == predicate_iri]


def test_rml_object_map_constant_iri_is_emitted_as_iri(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
@prefix rml: <http://w3id.org/rml/> .
@prefix rr:  <http://www.w3.org/ns/r2rml#> .
@prefix ql:  <http://semweb.mmlab.be/ns/ql#> .
@prefix ex:  <http://example.com/> .

<#M>
  rml:logicalSource [ rml:source "data.csv" ; rml:referenceFormulation ql:CSV ] ;
  rr:subjectMap [ rr:template "http://example.com/s/{id}" ] ;
  rr:predicateObjectMap [ rr:predicate ex:p ; rr:objectMap [ rr:constant ex:Obj ] ] .
""".strip(),
    )
    obj = _objects_for_predicate(graph, "http://example.com/p")[0]
    assert isinstance(obj, URIRef)
    assert str(obj) == "http://example.com/Obj"


def test_rml_object_literal_language_is_preserved_for_rr_object_shortcut(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
@prefix rml: <http://w3id.org/rml/> .
@prefix rr:  <http://www.w3.org/ns/r2rml#> .
@prefix ql:  <http://semweb.mmlab.be/ns/ql#> .
@prefix ex:  <http://example.com/> .

<#M>
  rml:logicalSource [ rml:source "data.csv" ; rml:referenceFormulation ql:CSV ] ;
  rr:subjectMap [ rr:template "http://example.com/s/{id}" ] ;
  rr:predicateObjectMap [ rr:predicate ex:p ; rr:object "hello"@en ] .
""".strip(),
    )
    obj = _objects_for_predicate(graph, "http://example.com/p")[0]
    assert isinstance(obj, Literal)
    assert obj.language == "en"
    assert str(obj) == "hello"


def test_rml_object_literal_datatype_is_preserved_for_rr_object_shortcut(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
@prefix rml: <http://w3id.org/rml/> .
@prefix rr:  <http://www.w3.org/ns/r2rml#> .
@prefix ql:  <http://semweb.mmlab.be/ns/ql#> .
@prefix ex:  <http://example.com/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<#M>
  rml:logicalSource [ rml:source "data.csv" ; rml:referenceFormulation ql:CSV ] ;
  rr:subjectMap [ rr:template "http://example.com/s/{id}" ] ;
  rr:predicateObjectMap [ rr:predicate ex:p ; rr:object "1"^^xsd:integer ] .
""".strip(),
    )
    obj = _objects_for_predicate(graph, "http://example.com/p")[0]
    assert isinstance(obj, Literal)
    assert obj.datatype == XSD.integer
    assert str(obj) == "1"
