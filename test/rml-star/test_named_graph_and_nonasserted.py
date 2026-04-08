from __future__ import annotations

import os

import morph_kgc


def test_named_graph_triples_map_is_not_materialized_in_current_contract():
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "r2rml", "R2RMLTC0006a")
    mapping_path = os.path.join(base_dir, "mapping.ttl")
    db_path = os.path.join(base_dir, "resource.db")
    config = (
        "[CONFIGURATION]\noutput_format=N-QUADS\n[DataSource]\n"
        f"mappings={mapping_path}\n"
        f"db_url=sqlite:///{db_path}"
    )

    graph = morph_kgc.materialize(config)
    triple_set = morph_kgc.materialize_set(config)

    assert len(graph) == 0
    assert triple_set == set()


def test_non_asserted_triples_map_does_not_emit_plain_assertion():
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RMLSTARTC005a")
    mapping_path = os.path.join(base_dir, "mapping.ttl")
    config = f"[CONFIGURATION]\noutput_format=N-QUADS\n[DataSource]\nmappings={mapping_path}"

    triple_set = morph_kgc.materialize_set(config)

    expected_quoted = "<< <http://example/s> <http://example/p> <http://example/o> >> <http://example/q> <http://example/z> "
    unexpected_plain = "<http://example/s> <http://example/p> <http://example/o> "

    assert expected_quoted in triple_set
    assert unexpected_plain not in triple_set
