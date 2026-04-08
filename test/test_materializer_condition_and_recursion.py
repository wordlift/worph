from __future__ import annotations

import pytest

from worph.core.model import LogicalSource, MappingDocument, TermMap, TriplesMap
from worph.core.sources import Record
from worph.materializer import _is_truthy, materialize_set_from_mapping


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        ("1", True),
        ("0", False),
        ("true", True),
        ("false", False),
        ("off", False),
        ("yes", True),
        ("", False),
        (None, False),
    ],
)
def test_is_truthy_matrix(value, expected) -> None:
    assert _is_truthy(value) is expected


def test_self_referencing_quoted_triples_map_does_not_recurse_forever(monkeypatch) -> None:
    tm = TriplesMap(
        identifier="tm1",
        logical_source=LogicalSource(source="dummy.csv", reference_formulation="csv"),
        subject_map=TermMap(template="http://example.com/{id}"),
        subject_quoted_triples_map="tm1",
        po_maps=[],
    )
    mapping = MappingDocument(prefixes={}, base=None, triples_maps=[tm])

    def _fake_iter_records(**kwargs):
        yield Record(values={"id": "1"})

    monkeypatch.setattr("worph.materializer.iter_records", _fake_iter_records)

    assert materialize_set_from_mapping(mapping) == set()
