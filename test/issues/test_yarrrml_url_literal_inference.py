from __future__ import annotations

import worph as morph_kgc
from rdflib import Literal, URIRef


def _materialize_from_mapping(tmp_path, mapping_body: str):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,slug\n1,faq\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(mapping_body.format(csv=csv_path.as_posix()), encoding="utf-8")
    config = f"[DataSource]\nmappings={mapping_path.as_posix()}"
    return morph_kgc.materialize(config)


def _object_for_predicate(graph, predicate_iri: str):
    for _, predicate, object_ in graph:
        if str(predicate) == predicate_iri:
            return object_
    raise AssertionError(f"predicate not found: {predicate_iri}")


def test_yarrrml_url_constant_with_datatype_string_is_literal(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
  xsd: "http://www.w3.org/2001/XMLSchema#"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/faq/"
            datatype: xsd:string
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, Literal)
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_url_template_with_datatype_string_is_literal(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
  xsd: "http://www.w3.org/2001/XMLSchema#"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/$(slug)/"
            datatype: xsd:string
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, Literal)
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_url_constant_with_language_is_literal(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/faq/"
            language: en
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, Literal)
    assert object_.language == "en"
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_url_template_with_language_is_literal(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/$(slug)/"
            language: en
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, Literal)
    assert object_.language == "en"
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_url_constant_without_datatype_or_language_is_inferred_iri(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/faq/"
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, URIRef)
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_explicit_type_iri_is_preserved(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv}~csv"
    s: "http://example.com/page/$(id)"
    po:
      - p: ex:url
        o:
          - value: "https://example.com/faq/"
            type: iri
""",
    )
    object_ = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(object_, URIRef)
    assert str(object_) == "https://example.com/faq/"


def test_yarrrml_schema_url_faq_like_mapping_emits_literal(tmp_path):
    graph = _materialize_from_mapping(
        tmp_path,
        """
prefixes:
  schema: "http://schema.org/"
  xsd: "http://www.w3.org/2001/XMLSchema#"
mappings:
  faq_static:
    sources:
      - "{csv}~csv"
    s: "https://example.com/page/$(id)"
    po:
      - p: schema:url
        o:
          - value: "https://example.com/faq/"
            datatype: xsd:string
""",
    )
    object_ = _object_for_predicate(graph, "http://schema.org/url")
    assert isinstance(object_, Literal)
    assert str(object_) == "https://example.com/faq/"
