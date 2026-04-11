from __future__ import annotations

from pathlib import Path

from worph.core import yarrrml as y


def test_parse_compact_source_and_source_item_variants():
    assert y._parse_compact_source(" file.csv~CSV ") == {
        "access": "file.csv",
        "referenceFormulation": "csv",
    }
    assert y._parse_compact_source("file.csv") == {"access": "file.csv", "referenceFormulation": "csv"}

    aliases = {"main": {"access": "a.csv", "referenceFormulation": "csv"}}
    assert y._parse_source_item("main", aliases) == aliases["main"]
    assert y._parse_source_item([], aliases) is None
    assert y._parse_source_item(["main", "/x", "SELECT 1"], aliases) == {
        "access": "a.csv",
        "referenceFormulation": "csv",
        "iterator": "/x",
        "query": "SELECT 1",
    }
    assert y._parse_source_item({"table": "t", "queryFormulation": "csv"}, aliases) == {
        "queryFormulation": "csv",
        "query": "SELECT * FROM t",
        "referenceFormulation": "csv",
    }
    assert y._parse_source_item(7, aliases) is None


def test_normalize_sources_variants():
    aliases = {"main": {"access": "a.csv", "referenceFormulation": "csv"}}
    assert y._normalize_sources(None, aliases) == []
    assert y._normalize_sources("main", aliases) == [{"access": "a.csv", "referenceFormulation": "csv"}]
    assert y._normalize_sources({"access": "a.csv"}, aliases) == [{"access": "a.csv"}]
    assert y._normalize_sources(["main", 7], aliases) == [{"access": "a.csv", "referenceFormulation": "csv"}]
    assert y._normalize_sources(12.5, aliases) == []


def test_normalize_po_key_and_expand_prefixed():
    mapping = {
        "po": [
            {"p": "ex:p", "o": "x"},
            ["ex:q", "$(v)"],
            ["ex:r", "v", "iri"],
            ["ex:s", "v", "xsd:string"],
            ["ex:t", "v", "en~lang"],
            ["ex:u", "v", "$(lang)~lang"],
        ]
    }
    normalized = y._normalize_po_key(mapping)
    assert normalized[0]["p"] == "ex:p"
    assert normalized[1] == {"p": "ex:q", "o": "$(v)"}
    assert normalized[2] == {"p": "ex:r", "o": {"value": "v", "type": "iri"}}
    assert normalized[3] == {"p": "ex:s", "o": {"value": "v", "datatype": "xsd:string"}}
    assert normalized[4] == {"p": "ex:t", "o": {"value": "v", "language": "en"}}
    assert normalized[5] == {"p": "ex:u", "o": {"value": "v", "language": "$(lang)"}}
    assert y._normalize_po_key({"predicateobjects": [{"p": "a", "o": "b"}]}) == [{"p": "a", "o": "b"}]
    assert y._normalize_po_key({"predicateObjects": [{"p": "a", "o": "b"}]}) == [{"p": "a", "o": "b"}]
    assert y._normalize_po_key({"po": "bad"}) == []

    prefixes = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "ex": "http://example.com/"}
    assert y._expand_prefixed(1, prefixes) == 1
    assert y._expand_prefixed("https://e", prefixes) == "https://e"
    assert y._expand_prefixed("<https://e>", prefixes) == "https://e"
    assert y._expand_prefixed("$(id)", prefixes) == "$(id)"
    assert y._expand_prefixed("a", prefixes) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    assert y._expand_prefixed("ex:p", prefixes) == "http://example.com/p"
    assert y._expand_prefixed("plain", prefixes) == "plain"


def test_parse_function_call_and_term_map_variants():
    prefixes = {"ex": "http://example.com/", "xsd": "http://www.w3.org/2001/XMLSchema#"}
    external = {"v": "external", "id": "99", "lang": "en"}
    call = y._parse_function_call(
        {
            "function": "ex:fn",
            "parameters": [
                "skip",
                {"parameter": None, "value": "x"},
                {"parameter": "ex:p0", "value": {"function": "ex:nested", "parameters": []}},
                {"parameter": "ex:p1", "value": "$(v)"},
                {"parameter": "ex:p2", "value": "$(\\_id)"},
                {"parameter": "ex:p3", "value": "ex:$(id)"},
                {"parameter": "ex:p4", "value": True},
                {"parameter": "ex:p5", "value": 42},
            ],
        },
        prefixes,
        external,
    )
    assert call.function_iri == "http://example.com/fn"
    assert len(call.parameters) == 6
    assert call.parameters[0][1].function_iri == "http://example.com/nested"
    assert call.parameters[1][1] == "external"
    assert call.parameters[2][1] == "99"
    assert call.parameters[3][1]["template"] == "http://example.com/{id}"
    assert call.parameters[4][1] == "true"
    assert call.parameters[5][1] == "42"

    short_call = y._parse_function_call(
        {"function": "ex:toLower(ex:p = ex:color_$(id))"},
        prefixes,
        external,
    )
    assert short_call.function_iri == "http://example.com/toLower"
    assert short_call.parameters[0][0] == "http://example.com/p"
    assert short_call.parameters[0][1]["template"] == "http://example.com/color_{id}"

    assert y._yarrrml_template_to_rr("x $( id ) y") == "x {id} y"

    tm = y._term_map_from_object_spec("$(v)", prefixes, external)
    assert tm.constant == "external" and tm.term_type == "literal"
    tm = y._term_map_from_object_spec("$(\\_id)", prefixes, external)
    assert tm.constant == "99"
    tm = y._term_map_from_object_spec("$(new)~iri", prefixes, external)
    assert tm.reference == "new" and tm.term_type == "iri"
    tm = y._term_map_from_object_spec("ex:$(id)", prefixes, external)
    assert tm.template == "http://example.com/{id}" and tm.term_type == "iri"
    tm = y._term_map_from_object_spec("urn:faq:$(id)", prefixes, external)
    assert tm.template == "urn:faq:{id}" and tm.term_type == "iri"
    tm = y._term_map_from_object_spec("$raw", prefixes, external)
    assert tm.template == "$raw"
    tm = y._term_map_from_object_spec("https://example.com", prefixes, external)
    assert tm.term_type == "iri"
    tm = y._term_map_from_object_spec(7, prefixes, external)
    assert tm.constant == 7 and tm.term_type == "literal"

    fn_tm = y._term_map_from_object_spec(
        {"function": "ex:fn", "parameters": [], "type": "iri", "datatype": "xsd:string", "language": "en"},
        prefixes,
        external,
    )
    assert fn_tm.term_type == "iri"
    fn_tm_upper = y._term_map_from_object_spec(
        {"function": "ex:fn", "parameters": [], "type": "IRI"},
        prefixes,
        external,
    )
    assert fn_tm_upper.term_type == "iri"
    assert fn_tm.datatype == "http://www.w3.org/2001/XMLSchema#string"
    assert fn_tm.language == "en"

    ref_tm = y._term_map_from_object_spec({"value": "$(v)", "datatype": "xsd:string"}, prefixes, external)
    assert ref_tm.constant == "external"
    ref_tm = y._term_map_from_object_spec({"value": "https://example.com/$(id)", "datatype": "xsd:string"}, prefixes, external)
    assert ref_tm.template == "https://example.com/{id}" and ref_tm.term_type == "literal"
    ref_tm = y._term_map_from_object_spec({"value": "ex:$(id)", "datatype": "xsd:string"}, prefixes, external)
    assert ref_tm.template == "http://example.com/{id}" and ref_tm.term_type == "literal"
    ref_tm = y._term_map_from_object_spec({"value": "https://example.com", "type": "iri"}, prefixes, external)
    assert ref_tm.term_type == "iri"
    lang_tm = y._term_map_from_object_spec({"value": "x", "language": "en"}, prefixes, external)
    assert lang_tm.language == "en"
    assert lang_tm.language_map is None
    lang_ref_tm = y._term_map_from_object_spec({"value": "x", "language": "$(row_lang)"}, prefixes, external)
    assert lang_ref_tm.language is None
    assert lang_ref_tm.language_map is not None
    assert lang_ref_tm.language_map.reference == "row_lang"
    lang_external_tm = y._term_map_from_object_spec({"value": "x", "language": "$(lang)"}, prefixes, external)
    assert lang_external_tm.language == "en"
    assert lang_external_tm.language_map is None
    lang_template_tm = y._term_map_from_object_spec({"value": "x", "language": "$(lang)-$(id)"}, prefixes, external)
    assert lang_template_tm.language is None
    assert lang_template_tm.language_map is not None
    assert lang_template_tm.language_map.template == "{lang}-{id}"
    assert y._term_map_from_object_spec({"x": 1}, prefixes, external).term_type == "literal"


def test_build_po_map_mapping_and_condition_parsing():
    prefixes = {"ex": "http://example.com/"}
    po = y._build_po_map(
        {
            "p": "ex:p",
            "o": {
                "mapping": "parent",
                "condition": {
                    "function": "equal",
                    "parameters": [["str1", "$(child)", "s"], ["str2", "$(parent)", "o"]],
                },
            },
            "condition": {"function": "ex:cond", "parameters": []},
        },
        prefixes,
        {},
    )
    assert po.predicate_maps[0].constant == "http://example.com/p"
    assert po.object_maps[0].parent_triples_map == "yarrrml:parent"
    assert po.object_maps[0].join_conditions[0].child == "child"
    assert po.object_maps[0].join_conditions[0].parent == "parent"
    assert po.condition is not None

    po_dict_condition = y._build_po_map(
        {
            "p": "ex:p",
            "o": {
                "mapping": "parent",
                "condition": {
                    "function": "equal",
                    "parameters": [
                        {"parameter": "str1", "value": "$(child)"},
                        {"parameter": "str2", "value": "$(parent)"},
                    ],
                },
            },
        },
        prefixes,
        {},
    )
    assert po_dict_condition.object_maps[0].join_conditions[0].child == "child"
    assert po_dict_condition.object_maps[0].join_conditions[0].parent == "parent"

    po_qualified_mapping = y._build_po_map({"p": "ex:p", "o": {"mapping": "yarrrml:parent"}}, prefixes, {})
    assert po_qualified_mapping.object_maps[0].parent_triples_map == "yarrrml:parent"

    po_without_mapping = y._build_po_map({"predicates": "ex:q", "objects": "$(x)"}, prefixes, {})
    assert po_without_mapping.object_maps[0].term_map.reference == "x"


def test_parse_yarrrml_path_overrides_and_aliases(tmp_path, monkeypatch):
    rel_file = tmp_path / "input.csv"
    rel_file.write_text("id\n1\n", encoding="utf-8")
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
sources:
  main:
    access: "{rel_file.name}"
    referenceFormulation: "CSV"
mappings:
  m1:
    sources:
      - main
    subjects:
      - "http://example.com/s/$(id)"
    po:
      - [ex:p, "v"]
  skipme: 7
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(y.os.path, "exists", lambda _: False)
    doc = y.parse_yarrrml(mapping_path.as_posix())
    tm = doc.triples_maps[0]
    assert tm.logical_source.source == (tmp_path / rel_file.name).as_posix()
    assert tm.logical_source.reference_formulation == "csv"
    assert tm.subject_map.term_type == "iri"

    doc_override = y.parse_yarrrml(
        mapping_path.as_posix(),
        file_path_override=(tmp_path / rel_file.name).as_posix(),
    )
    assert doc_override.triples_maps[0].logical_source.source == (tmp_path / rel_file.name).as_posix()

    empty_source_mapping = tmp_path / "mapping-empty.yarrrml"
    empty_source_mapping.write_text(
        """
mappings:
  m1:
    s: "http://example.com/s"
    po:
      - [http://example.com/p, "v"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    db_doc = y.parse_yarrrml(empty_source_mapping.as_posix(), db_url_override="sqlite:////tmp/db.sqlite")
    assert db_doc.triples_maps[0].logical_source.source == "sqlite:////tmp/db.sqlite"


def test_parse_yarrrml_uses_existing_relative_path_when_present(tmp_path, monkeypatch):
    mapping_path = tmp_path / "mapping.yarrrml"
    mapping_path.write_text(
        """
sources:
  main: "exists.csv~csv"
mappings:
  m1:
    sources:
      - main
    s: "http://example.com/s"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(y.os.path, "exists", lambda p: p == "exists.csv")
    doc = y.parse_yarrrml(mapping_path.as_posix())
    assert doc.triples_maps[0].logical_source.source == "exists.csv"
