from __future__ import annotations

from xml.etree import ElementTree as ET

from worph.core.sources import _normalize_xpath, _xpath_values, iter_records, iter_xml


def test_xpath_undefined_prefix_falls_back_to_local_name() -> None:
    root = ET.fromstring("<root xmlns:ns='urn:x'><item><ns:name>A</ns:name></item></root>")
    item = root.find("item")
    assert item is not None

    values = _xpath_values(item, "foo:name")

    assert values == ["A"]


def test_xpath_malformed_expression_returns_empty_list() -> None:
    root = ET.fromstring("<root><item>A</item></root>")

    assert _xpath_values(root, "//*[") == []


def test_xpath_normalization_does_not_rewrite_predicate_attributes() -> None:
    expr = "//meta[@property='og:title']"

    assert _normalize_xpath(expr) == expr


def test_xpath_normalization_does_not_rewrite_shorthand_after_predicate() -> None:
    expr = "country[neighbor='BE']/neighbor@name"

    assert _normalize_xpath(expr) == expr


def test_xpath_normalization_does_not_rewrite_at_inside_literal() -> None:
    expr = "//*[contains(name(),'@')]"

    assert _normalize_xpath(expr) == expr


def test_xpath_normalization_does_not_rewrite_shorthand_when_other_attribute_axis_exists() -> None:
    expr = "a/@id/b@c"

    assert _normalize_xpath(expr) == expr


def test_xml_root_iterator_slash_yields_root_record(tmp_path) -> None:
    xml_path = tmp_path / "source.xhtml"
    xml_path.write_text("<html><head><title>T</title></head></html>", encoding="utf-8")

    rows = list(iter_xml(str(xml_path), "/"))

    assert len(rows) == 1
    assert rows[0].context is not None


def test_csv_query_read_csv_variant_parses_case_and_delimiter(tmp_path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("ID;COL\n1;['a','b']\n2;['c']\n", encoding="utf-8")
    query = (
        "SELECT ID, UNNEST(COL::VARCHAR[]) AS COL "
        f"FROM READ_CSV('{csv_path.as_posix()}', delim=';')"
    )

    rows = list(iter_records(formulation="csv", source=str(csv_path), query=query))

    assert [row.values["COL"] for row in rows] == ["a", "b", "c"]
    assert [row.values["ID"] for row in rows] == ["1", "1", "2"]
