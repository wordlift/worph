from __future__ import annotations

import os
from io import BytesIO

import morph_kgc
from pyoxigraph import Store


def test_quoted_triple_materialize_vs_set_contract():
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RMLSTARTC001a")
    mapping_path = os.path.join(base_dir, "mapping.ttl")
    config = f"[CONFIGURATION]\noutput_format=N-QUADS\n[DataSource]\nmappings={mapping_path}"

    graph = morph_kgc.materialize(config)
    triple_set = morph_kgc.materialize_set(config)

    assert len(graph) == 1
    assert len(triple_set) == 2
    assert any(line.startswith("<< ") for line in triple_set)
    assert any("<http://example/p> <http://example/o>" in line and not line.startswith("<< ") for line in triple_set)


def test_quoted_triple_set_and_oxigraph_modes_are_equivalent():
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RMLSTARTC003a")
    mapping_path = os.path.join(base_dir, "mapping.ttl")
    config = f"[CONFIGURATION]\noutput_format=N-QUADS\n[DataSource]\nmappings={mapping_path}"

    triple_set = morph_kgc.materialize_set(config)
    graph_oxigraph = morph_kgc.materialize_oxigraph(config)

    from_set = Store()
    if triple_set:
        payload = ".\n".join(sorted(triple_set)) + "."
        from_set.bulk_load(BytesIO(payload.encode("utf-8")), "application/n-quads")

    assert set(from_set) == set(graph_oxigraph)
