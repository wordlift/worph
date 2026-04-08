from __future__ import annotations

import pytest

import morph_kgc


def test_translate_to_rml_returns_mapping_path_string(tmp_path):
    mapping_path = tmp_path / "mapping.ttl"
    mapping_path.write_text("", encoding="utf-8")

    translated = morph_kgc.translate_to_rml(str(mapping_path))

    assert translated == str(mapping_path)


def test_translate_to_rml_keeps_non_existing_path_as_string():
    missing_path = "does/not/exist/mapping.ttl"

    translated = morph_kgc.translate_to_rml(missing_path)

    assert translated == missing_path


def test_materialize_kafka_is_not_implemented():
    with pytest.raises(NotImplementedError, match="not implemented"):
        morph_kgc.materialize_kafka("[DataSource]\nmappings=dummy.ttl")
