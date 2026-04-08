from __future__ import annotations

import morph_kgc
import pytest


@pytest.mark.parametrize("po_key", ["po", "predicateobjects", "predicateObjects"])
def test_condition_syntax_variants_po_p_o_list(tmp_path, po_key):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,flag\n1,Alice,yes\n2,Bob,no\n", encoding="utf-8")

    mapping_path = tmp_path / f"mapping-{po_key}.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    {po_key}:
      - p: ex:name
        o: $(name)
        condition:
          function: equal
          parameters:
            - parameter: str1
              value: $(flag)
            - parameter: str2
              value: "yes"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping_path.as_posix()}"
    graph = morph_kgc.materialize(config)

    subjects = {str(subject) for subject, _, _ in graph}
    assert subjects == {"http://example.com/person/1"}


def test_condition_false_branch_filters_all_rows(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,flag\n1,Alice,no\n2,Bob,no\n", encoding="utf-8")

    mapping_path = tmp_path / "mapping-false.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    po:
      - p: ex:name
        o: $(name)
        condition:
          function: equal
          parameters:
            - parameter: str1
              value: $(flag)
            - parameter: str2
              value: "yes"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping_path.as_posix()}"
    graph = morph_kgc.materialize(config)

    assert len(graph) == 0


def test_unknown_condition_function_is_non_crashing_and_filters_out(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,flag\n1,Alice,yes\n", encoding="utf-8")

    mapping_path = tmp_path / "mapping-unknown-condition.yarrrml"
    mapping_path.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{csv_path.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    po:
      - p: ex:name
        o: $(name)
        condition:
          function: ex:missingConditionFunction
          parameters:
            - parameter: ex:arg
              value: $(flag)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping_path.as_posix()}"
    graph = morph_kgc.materialize(config)

    assert len(graph) == 0
