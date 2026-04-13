from __future__ import annotations

from pathlib import Path

from rdflib import URIRef

from worph.core.yarrrml import parse_yarrrml
from worph.materializer import materialize_from_mapping


def _write_mapping(tmp_path: Path, mapping_name: str, mapping_body: str) -> Path:
    mapping_path = tmp_path / mapping_name
    mapping_path.write_text(mapping_body.strip() + "\n", encoding="utf-8")
    return mapping_path


def _materialize(mapping_path: Path):
    mapping = parse_yarrrml(mapping_path.as_posix())
    return materialize_from_mapping(mapping)


def test_itemlist_xpath_concat_regression_cases(tmp_path: Path) -> None:
    html_path = tmp_path / "source.xhtml"
    html_path.write_text(
        """
<html>
  <body>
    <h1>Coach Buses For Sale</h1>
    <div class="product-item"><h3 class="product-title"><a href="/buses/a">A</a></h3></div>
    <div class="product-item"><h3 class="product-title"><a href="/buses/b">B</a></h3></div>
  </body>
</html>
""".strip()
        + "\n",
        encoding="utf-8",
    )

    common = f"""
prefixes:
  schema: http://schema.org/
  xsd: http://www.w3.org/2001/XMLSchema#
sources:
  source:
    access: {html_path.as_posix()}
    referenceFormulation: xpath
    iterator: /html
mappings:
  collection_item_list:
    sources:
      - source
    s: https://data.example.test/item-list
    po:
      - - a
        - schema:ItemList
"""

    control_map = _write_mapping(
        tmp_path,
        "control.yarrrml",
        common
        + """
      - p: schema:itemListElement
        o:
          - value: $(//div[contains(concat(' ', normalize-space(@class), ' '), ' product-item ')]//h3[contains(concat(' ', normalize-space(@class), ' '), ' product-title ')]//a[starts-with(@href, '/buses/')]/@href)
            datatype: xsd:string
""",
    )
    iri_concat_map = _write_mapping(
        tmp_path,
        "failing_itemlist_iri_concat.yarrrml",
        common
        + """
      - p: schema:itemListElement
        o:
          - value: https://data.example.test$(//div[contains(concat(' ', normalize-space(@class), ' '), ' product-item ')]//h3[contains(concat(' ', normalize-space(@class), ' '), ' product-title ')]//a[starts-with(@href, '/buses/')]/@href)
            type: iri
""",
    )
    schema_url_map = _write_mapping(
        tmp_path,
        "failing_schema_url_concat.yarrrml",
        common
        + """
      - p: schema:url
        o:
          - value: $(concat('https://data.example.test', //div[contains(concat(' ', normalize-space(@class), ' '), ' product-item ')]//h3[contains(concat(' ', normalize-space(@class), ' '), ' product-title ')]//a[starts-with(@href, '/buses/')]/@href))
            datatype: xsd:string
""",
    )

    subject = URIRef("https://data.example.test/item-list")
    item_list_element = URIRef("http://schema.org/itemListElement")
    schema_url = URIRef("http://schema.org/url")

    control_graph = _materialize(control_map)
    control_values = sorted(str(obj) for _, _, obj in control_graph.triples((subject, item_list_element, None)))
    assert control_values == ["/buses/a", "/buses/b"]

    iri_concat_graph = _materialize(iri_concat_map)
    iri_concat_values = sorted(str(obj) for _, _, obj in iri_concat_graph.triples((subject, item_list_element, None)))
    assert iri_concat_values == ["https://data.example.test/buses/a", "https://data.example.test/buses/b"]

    schema_url_graph = _materialize(schema_url_map)
    schema_url_values = sorted(str(obj) for _, _, obj in schema_url_graph.triples((subject, schema_url, None)))
    assert schema_url_values == ["https://data.example.test/buses/a", "https://data.example.test/buses/b"]
