from __future__ import annotations

from worph.core.config import RuntimeConfig
from worph.core.loader import load_mapping


def _runtime_config() -> RuntimeConfig:
    import configparser

    return RuntimeConfig(
        parser=configparser.ConfigParser(interpolation=None),
        source_path=None,
        mappings=[],
        file_path="/tmp/data.csv",
        db_url="sqlite:////tmp/db.sqlite",
        output_format="N-TRIPLES",
        output_file=None,
        udfs=[],
    )


def test_load_mapping_dispatches_yarrrml_loader_and_forwards_overrides(monkeypatch) -> None:
    config = _runtime_config()
    captured = {}

    monkeypatch.setattr("worph.core.loader._resolve_mapping_path", lambda *_: "/tmp/mapping.yarrrml")

    def _fake_yarrrml_loader(resolved, cfg):
        captured["resolved"] = resolved
        captured["file_path"] = cfg.file_path
        captured["db_url"] = cfg.db_url
        return "yarrrml-doc"

    monkeypatch.setitem(__import__("worph.core.loader", fromlist=["_PARSER_LOADERS"])._PARSER_LOADERS, "yarrrml", _fake_yarrrml_loader)

    result = load_mapping("ignored", config)

    assert result == "yarrrml-doc"
    assert captured == {
        "resolved": "/tmp/mapping.yarrrml",
        "file_path": "/tmp/data.csv",
        "db_url": "sqlite:////tmp/db.sqlite",
    }


def test_load_mapping_dispatches_rml_loader_and_forwards_overrides(monkeypatch) -> None:
    config = _runtime_config()
    captured = {}

    monkeypatch.setattr("worph.core.loader._resolve_mapping_path", lambda *_: "/tmp/mapping.ttl")

    def _fake_rml_loader(resolved, cfg):
        captured["resolved"] = resolved
        captured["file_path"] = cfg.file_path
        captured["db_url"] = cfg.db_url
        return "rml-doc"

    monkeypatch.setitem(__import__("worph.core.loader", fromlist=["_PARSER_LOADERS"])._PARSER_LOADERS, "rml", _fake_rml_loader)

    result = load_mapping("ignored", config)

    assert result == "rml-doc"
    assert captured == {
        "resolved": "/tmp/mapping.ttl",
        "file_path": "/tmp/data.csv",
        "db_url": "sqlite:////tmp/db.sqlite",
    }
