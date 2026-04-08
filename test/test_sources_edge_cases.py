from __future__ import annotations

from xml.etree import ElementTree as ET

from worph.core.sources import _xpath_values, iter_records


def test_xpath_undefined_prefix_falls_back_to_local_name() -> None:
    root = ET.fromstring("<root xmlns:ns='urn:x'><item><ns:name>A</ns:name></item></root>")
    item = root.find("item")
    assert item is not None

    values = _xpath_values(item, "foo:name")

    assert values == ["A"]


def test_xpath_malformed_expression_returns_empty_list() -> None:
    root = ET.fromstring("<root><item>A</item></root>")

    assert _xpath_values(root, "//*[") == []


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
