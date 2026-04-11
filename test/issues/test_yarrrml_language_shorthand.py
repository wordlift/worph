from __future__ import annotations

import worph as morph_kgc
from rdflib import Literal


def _object_for_predicate(graph, predicate_iri: str):
    for _, predicate, object_ in graph:
        if str(predicate) == predicate_iri:
            return object_
    raise AssertionError(f"predicate not found: {predicate_iri}")


def test_yarrrml_fixed_language_shorthand_emits_lang_literal(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name\n1,Hello\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/s/$(id)"
    po:
      - [ex:label, "$(name)", "en~lang"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    graph = morph_kgc.materialize(f"[DataSource]\nmappings={mapping_path.as_posix()}")
    obj = _object_for_predicate(graph, "http://example.com/label")
    assert isinstance(obj, Literal)
    assert str(obj) == "Hello"
    assert obj.language == "en"


def test_yarrrml_dynamic_language_shorthand_uses_reference_value(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,lang\n1,Hello,fr\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/s/$(id)"
    po:
      - [ex:label, "$(name)", "$(lang)~lang"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    graph = morph_kgc.materialize(f"[DataSource]\nmappings={mapping_path.as_posix()}")
    obj = _object_for_predicate(graph, "http://example.com/label")
    assert isinstance(obj, Literal)
    assert str(obj) == "Hello"
    assert obj.language == "fr"


def test_yarrrml_dynamic_language_keeps_url_value_literal(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,path,lang\n1,faq,fr\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/s/$(id)"
    po:
      - [ex:url, "https://example.com/$(path)/", "$(lang)~lang"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    graph = morph_kgc.materialize(f"[DataSource]\nmappings={mapping_path.as_posix()}")
    obj = _object_for_predicate(graph, "http://example.com/url")
    assert isinstance(obj, Literal)
    assert str(obj) == "https://example.com/faq/"
    assert obj.language == "fr"


def test_yarrrml_language_reference_can_resolve_external_value(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name\n1,Hello\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
external:
  lang: en
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/s/$(id)"
    po:
      - p: ex:label
        o:
          - value: "$(name)"
            language: "$(lang)"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    graph = morph_kgc.materialize(f"[DataSource]\nmappings={mapping_path.as_posix()}")
    obj = _object_for_predicate(graph, "http://example.com/label")
    assert isinstance(obj, Literal)
    assert str(obj) == "Hello"
    assert obj.language == "en"
