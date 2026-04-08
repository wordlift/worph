from __future__ import annotations

import morph_kgc


def test_unknown_function_returns_none_without_crash(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name\n1,alpha\n", encoding="utf-8")

    mapping_path = tmp_path / "mapping.yarrrml"
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
      - p: ex:value
        o:
          function: ex:notRegisteredFunction
          parameters:
            - parameter: ex:arg
              value: $(name)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = f"[DataSource]\nmappings:{mapping_path.as_posix()}"
    graph = morph_kgc.materialize(config)

    assert len(graph) == 0
