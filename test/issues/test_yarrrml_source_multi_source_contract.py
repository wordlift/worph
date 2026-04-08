from __future__ import annotations

import morph_kgc
import pytest


def test_yarrrml_multiple_sources_materialization_contract(tmp_path):
    first_csv = tmp_path / "first.csv"
    first_csv.write_text("id,name\n1,alpha\n", encoding="utf-8")

    second_csv = tmp_path / "second.csv"
    second_csv.write_text("id,name\n2,beta\n", encoding="utf-8")

    mapping = tmp_path / "mapping.yarrrml"
    mapping.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{first_csv.as_posix()}~csv"
      - "{second_csv.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    po:
      - [ex:name, $(name)]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping.as_posix()}"
    graph = morph_kgc.materialize(config)

    rendered = {str(subject) for subject, _, _ in graph}
    assert "http://example.com/person/1" in rendered
    assert "http://example.com/person/2" not in rendered


def test_yarrrml_multiple_sources_follow_first_item_order(tmp_path):
    first_csv = tmp_path / "first.csv"
    first_csv.write_text("id,name\n1,alpha\n", encoding="utf-8")

    second_csv = tmp_path / "second.csv"
    second_csv.write_text("id,name\n2,beta\n", encoding="utf-8")

    mapping = tmp_path / "mapping.yarrrml"
    mapping.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{second_csv.as_posix()}~csv"
      - "{first_csv.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    po:
      - [ex:name, $(name)]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping.as_posix()}"
    graph = morph_kgc.materialize(config)

    rendered = {str(subject) for subject, _, _ in graph}
    assert "http://example.com/person/2" in rendered
    assert "http://example.com/person/1" not in rendered


def test_yarrrml_invalid_first_source_raises_file_not_found(tmp_path):
    missing_csv = tmp_path / "missing.csv"
    existing_csv = tmp_path / "existing.csv"
    existing_csv.write_text("id,name\n1,alpha\n", encoding="utf-8")

    mapping = tmp_path / "mapping.yarrrml"
    mapping.write_text(
        f"""
prefixes:
  ex: "http://example.com/"
mappings:
  m1:
    sources:
      - "{missing_csv.as_posix()}~csv"
      - "{existing_csv.as_posix()}~csv"
    s: "http://example.com/person/$(id)"
    po:
      - [ex:name, $(name)]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping.as_posix()}"
    with pytest.raises(FileNotFoundError):
        morph_kgc.materialize(config)
