from __future__ import annotations

from rdflib import Literal, URIRef
from rdflib.namespace import XSD

from worph.core.emitter import _normalize_integer_lexical, render_node
from worph.core.model import TermMap


def test_url_literal_not_encoded_but_iri_is_encoded() -> None:
    raw = "https://example.com/a path/[x]"

    literal_node = render_node(raw, TermMap(term_type="literal"), role="object")
    iri_node = render_node(raw, TermMap(term_type="iri"), role="object")

    assert isinstance(literal_node, Literal)
    assert str(literal_node) == raw
    assert isinstance(iri_node, URIRef)
    assert str(iri_node) == "https://example.com/a%20path/[x]"


def test_language_takes_precedence_when_both_datatype_and_language_are_set() -> None:
    node = render_node(
        "hello",
        TermMap(term_type="literal", datatype=str(XSD.string), language="en"),
        role="object",
    )
    assert isinstance(node, Literal)
    assert node.language == "en"
    assert node.datatype is None


def test_integer_lexical_normalization_matrix() -> None:
    assert _normalize_integer_lexical("01") == "1"
    assert _normalize_integer_lexical("1.0") == "1"
    assert _normalize_integer_lexical(1.0) == "1"
    assert _normalize_integer_lexical(True) is None
    assert _normalize_integer_lexical("not-a-number") is None
