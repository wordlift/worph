from __future__ import annotations

from worph.core.sources import Record
from worph.core.term_map import _expand_template_values


def test_template_expansion_repeated_placeholder() -> None:
    record = Record(values={"id": "7"})

    values = _expand_template_values("http://example.com/{id}/{id}", record, "csv")

    assert values == ["http://example.com/7/7"]


def test_template_expansion_cartesian_product_for_list_values() -> None:
    record = Record(values={"a": ["x", "y"], "b": [1, 2]})

    values = _expand_template_values("{a}-{b}", record, "csv")

    assert values == ["x-1", "x-2", "y-1", "y-2"]


def test_template_expansion_preserves_escaped_braces() -> None:
    record = Record(values={"id": "7"})

    values = _expand_template_values(r"prefix\{literal\}-{id}", record, "csv")

    assert values == ["prefix{literal}-7"]
