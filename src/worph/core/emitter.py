from __future__ import annotations

from typing import Any
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.term import Node

from .model import TermMap

def render_node(value: Any, term_map: TermMap, role: str) -> Node | None:
    if value is None:
        return None

    value_as_text = str(value)
    term_type = (term_map.term_type or "").strip()
    term_type_lower = term_type.lower()

    if role == "predicate":
        return URIRef(_encode_iri(value_as_text))

    if term_type in {"BlankNode", "BNode"} or term_type_lower.endswith("blanknode"):
        return BNode(value_as_text)

    if term_type == "IRI" or term_type_lower.endswith("iri"):
        return URIRef(_encode_iri(value_as_text))

    if role == "subject":
        return URIRef(_encode_iri(value_as_text))

    if term_type == "Literal" or term_type_lower.endswith("literal"):
        return _build_literal(value, term_map)

    if term_map.datatype or term_map.language:
        return _build_literal(value, term_map)

    return Literal(value)


def emit_triple(graph: Graph, subject: Node | None, predicate: Node | None, object_: Node | None) -> None:
    if subject is None or predicate is None or object_ is None:
        return
    graph.add((subject, predicate, object_))


def _build_literal(value: Any, term_map: TermMap) -> Literal:
    datatype = URIRef(term_map.datatype) if term_map.datatype else None
    if term_map.language:
        return Literal(value, lang=term_map.language)
    if datatype is not None:
        if str(datatype) == "http://www.w3.org/2001/XMLSchema#string":
            # Legacy-compat behavior: xsd:string is emitted as plain literal.
            return Literal(value)
        if str(datatype) == "http://www.w3.org/2001/XMLSchema#integer":
            normalized = _normalize_integer_lexical(value)
            if normalized is not None:
                return Literal(normalized, datatype=datatype)
        return Literal(value, datatype=datatype)
    return Literal(value)


def _normalize_integer_lexical(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        as_float = float(text)
    except Exception:
        return text if text.lstrip("+-").isdigit() else None
    if as_float.is_integer():
        return str(int(as_float))
    return None


def _encode_iri(iri: str) -> str:
    return quote(iri, safe=":/?#[]@!$&'*+;=%")
