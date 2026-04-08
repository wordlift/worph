from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from rdflib.term import Node

from worph.core.config import parse_runtime_config
from worph.core.emitter import emit_triple, render_node
from worph.core.loader import load_mapping
from worph.core.model import MappingDocument, ObjectMapSpec, TriplesMap
from worph.core.sources import Record, iter_records, reference_value
from worph.core.term_map import render_term_map
from worph.fnml.engine import configure_udfs, evaluate_fnml_call


@dataclass(frozen=True, slots=True)
class QuotedTripleTerm:
    subject: "TermLike"
    predicate: Node
    object_: "TermLike"


TermLike: TypeAlias = Node | QuotedTripleTerm
TripleTerm: TypeAlias = tuple[TermLike, Node, TermLike]


@dataclass(slots=True)
class _RenderContext:
    mapping: MappingDocument
    rows_by_tm: dict[str, list[Record]]
    tm_by_id: dict[str, TriplesMap]
    subject_cache: dict[tuple[str, int], list[TermLike]]
    triples_cache: dict[tuple[str, int], list[TripleTerm]]
    in_progress: set[tuple[str, int]]


def materialize_from_mapping(
    mapping: MappingDocument,
    graph: Graph | None = None,
    python_source=None,
) -> Graph:
    rdf_graph = graph if graph is not None else Graph()
    asserted_triples = _build_asserted_triples(mapping, python_source=python_source)
    for subject, predicate, object_ in asserted_triples:
        if isinstance(subject, QuotedTripleTerm) or isinstance(object_, QuotedTripleTerm):
            continue
        emit_triple(rdf_graph, subject, predicate, object_)
    return rdf_graph


def materialize_set_from_mapping(mapping: MappingDocument, python_source=None) -> set[str]:
    asserted_triples = _build_asserted_triples(mapping, python_source=python_source)
    return {_serialize_triple_line(triple) for triple in asserted_triples}


def materialize_from_config(config_input: str | Path, python_source=None) -> Graph:
    runtime_config = parse_runtime_config(config_input)
    configure_udfs(runtime_config.udfs)
    merged = Graph()
    for mapping_path in runtime_config.mappings:
        mapping_doc = load_mapping(mapping_path, runtime_config)
        materialize_from_mapping(mapping_doc, graph=merged, python_source=python_source)
    return merged


def materialize_set_from_config(config_input: str | Path, python_source=None) -> set[str]:
    runtime_config = parse_runtime_config(config_input)
    configure_udfs(runtime_config.udfs)
    triples: set[str] = set()
    for mapping_path in runtime_config.mappings:
        mapping_doc = load_mapping(mapping_path, runtime_config)
        triples |= materialize_set_from_mapping(mapping_doc, python_source=python_source)
    return triples


def _build_asserted_triples(mapping: MappingDocument, python_source=None) -> list[TripleTerm]:
    rows_by_tm = _collect_rows(mapping, python_source=python_source)
    context = _RenderContext(
        mapping=mapping,
        rows_by_tm=rows_by_tm,
        tm_by_id={tm.identifier: tm for tm in mapping.triples_maps},
        subject_cache={},
        triples_cache={},
        in_progress=set(),
    )
    asserted: list[TripleTerm] = []
    for tm in mapping.triples_maps:
        if tm.has_named_graphs or not tm.asserted:
            continue
        rows = rows_by_tm.get(tm.identifier, [])
        for row_index in range(len(rows)):
            asserted.extend(_render_tm_row_triples(context, tm.identifier, row_index))
    return asserted


def _collect_rows(mapping: MappingDocument, python_source=None) -> dict[str, list[Record]]:
    rows_by_tm: dict[str, list[Record]] = {}
    for triples_map in mapping.triples_maps:
        if triples_map.has_named_graphs:
            continue
        formulation = triples_map.logical_source.reference_formulation
        rows = list(
            iter_records(
                formulation=formulation,
                source=triples_map.logical_source.source,
                iterator=triples_map.logical_source.iterator,
                query=triples_map.logical_source.query,
                namespaces=triples_map.logical_source.namespaces,
                python_source=python_source,
            )
        )
        rows_by_tm[triples_map.identifier] = rows
    return rows_by_tm


def _render_tm_row_triples(context: _RenderContext, tm_id: str, row_index: int) -> list[TripleTerm]:
    key = (tm_id, row_index)
    if key in context.triples_cache:
        return context.triples_cache[key]
    if key in context.in_progress:
        return []
    context.in_progress.add(key)
    triples_map = context.tm_by_id[tm_id]
    rows = context.rows_by_tm.get(tm_id, [])
    if row_index >= len(rows):
        context.in_progress.remove(key)
        context.triples_cache[key] = []
        return []
    record = rows[row_index]
    formulation = triples_map.logical_source.reference_formulation
    namespaces = triples_map.logical_source.namespaces

    subject_terms = _render_tm_row_subjects(context, tm_id, row_index)
    triples: list[TripleTerm] = []
    for subject_term in subject_terms:
        if not isinstance(subject_term, QuotedTripleTerm):
            for class_iri in triples_map.class_iris:
                class_node = render_node(class_iri, triples_map.subject_map, role="object")
                if class_node is not None:
                    triples.append((subject_term, RDF.type, class_node))

        for po_map in triples_map.po_maps:
            if po_map.condition is not None:
                cond_value = evaluate_fnml_call(
                    po_map.condition,
                    lambda ref: reference_value(
                        record,
                        formulation,
                        ref,
                        namespaces=namespaces,
                    ),
                )
                if not _is_truthy(cond_value):
                    continue

            predicate_nodes: list[Node] = []
            for predicate_tm in po_map.predicate_maps:
                p_value = render_term_map(
                    predicate_tm,
                    record,
                    formulation,
                    namespaces=namespaces,
                )
                p_node = render_node(p_value, predicate_tm, role="predicate")
                if p_node is not None:
                    predicate_nodes.append(p_node)

            object_terms: list[TermLike] = []
            for object_map in po_map.object_maps:
                object_terms.extend(
                    _render_tm_row_object_terms(
                        context=context,
                        object_map=object_map,
                        current_tm_id=tm_id,
                        current_row_index=row_index,
                    )
                )

            for p_node in predicate_nodes:
                for o_term in object_terms:
                    triples.append((subject_term, p_node, o_term))

    context.in_progress.remove(key)
    context.triples_cache[key] = triples
    return triples


def _render_tm_row_subjects(context: _RenderContext, tm_id: str, row_index: int) -> list[TermLike]:
    key = (tm_id, row_index)
    if key in context.subject_cache:
        return context.subject_cache[key]

    triples_map = context.tm_by_id[tm_id]
    rows = context.rows_by_tm.get(tm_id, [])
    if row_index >= len(rows):
        context.subject_cache[key] = []
        return []
    record = rows[row_index]

    if triples_map.subject_quoted_triples_map:
        terms = _quoted_terms_from_map(
            context=context,
            referenced_tm_id=triples_map.subject_quoted_triples_map,
            current_tm_id=tm_id,
            current_row_index=row_index,
        )
        context.subject_cache[key] = terms
        return terms

    formulation = triples_map.logical_source.reference_formulation
    subject_value = render_term_map(
        triples_map.subject_map,
        record,
        formulation,
        namespaces=triples_map.logical_source.namespaces,
    )
    values = subject_value if isinstance(subject_value, list) else [subject_value]
    subject_nodes = [render_node(v, triples_map.subject_map, role="subject") for v in values]
    terms = [node for node in subject_nodes if node is not None]
    context.subject_cache[key] = terms
    return terms


def _render_tm_row_object_terms(
    context: _RenderContext,
    object_map: ObjectMapSpec,
    current_tm_id: str,
    current_row_index: int,
) -> list[TermLike]:
    current_tm = context.tm_by_id[current_tm_id]
    current_rows = context.rows_by_tm.get(current_tm_id, [])
    if current_row_index >= len(current_rows):
        return []
    record = current_rows[current_row_index]
    formulation = current_tm.logical_source.reference_formulation
    namespaces = current_tm.logical_source.namespaces

    if object_map.quoted_triples_map:
        return _quoted_terms_from_map(
            context=context,
            referenced_tm_id=object_map.quoted_triples_map,
            current_tm_id=current_tm_id,
            current_row_index=current_row_index,
        )

    if object_map.parent_triples_map:
        parent_tm = context.tm_by_id.get(object_map.parent_triples_map)
        if parent_tm is None:
            return []
        parent_rows = context.rows_by_tm.get(parent_tm.identifier, [])
        terms: list[TermLike] = []

        if object_map.join_conditions:
            for parent_row_index, parent_record in enumerate(parent_rows):
                ok = True
                for jc in object_map.join_conditions:
                    child_val = reference_value(record, formulation, jc.child, namespaces=namespaces)
                    parent_val = reference_value(
                        parent_record,
                        parent_tm.logical_source.reference_formulation,
                        jc.parent,
                        namespaces=parent_tm.logical_source.namespaces,
                    )
                    if child_val != parent_val:
                        ok = False
                        break
                if ok:
                    terms.extend(_render_tm_row_subjects(context, parent_tm.identifier, parent_row_index))
            return terms

        if _same_logical_source(current_tm, parent_tm):
            terms.extend(_render_tm_row_subjects(context, parent_tm.identifier, current_row_index))
            return terms

        for parent_row_index in range(len(parent_rows)):
            terms.extend(_render_tm_row_subjects(context, parent_tm.identifier, parent_row_index))
        return terms

    if object_map.term_map is None:
        return []

    language = object_map.term_map.language
    if object_map.term_map.language_map is not None:
        lang_value = render_term_map(
            object_map.term_map.language_map,
            record,
            formulation,
            namespaces=namespaces,
        )
        if isinstance(lang_value, list):
            language = str(lang_value[0]) if lang_value else None
        elif lang_value is not None:
            language = str(lang_value)

    term_map = object_map.term_map
    if language != term_map.language:
        term_map = object_map.term_map.__class__(
            constant=term_map.constant,
            template=term_map.template,
            reference=term_map.reference,
            term_type=term_map.term_type,
            datatype=term_map.datatype,
            language=language,
            language_map=term_map.language_map,
            function_call=term_map.function_call,
        )

    value = render_term_map(term_map, record, formulation, namespaces=namespaces)
    if isinstance(value, list):
        terms: list[TermLike] = []
        for item in value:
            node = render_node(item, term_map, role="object")
            if node is not None:
                terms.append(node)
        return terms
    node = render_node(value, term_map, role="object")
    return [node] if node is not None else []


def _quoted_terms_from_map(
    context: _RenderContext,
    referenced_tm_id: str,
    current_tm_id: str,
    current_row_index: int,
) -> list[TermLike]:
    referenced_tm = context.tm_by_id.get(referenced_tm_id)
    current_tm = context.tm_by_id[current_tm_id]
    if referenced_tm is None:
        return []
    terms: list[TermLike] = []

    if _same_logical_source(current_tm, referenced_tm):
        triples = _render_tm_row_triples(context, referenced_tm.identifier, current_row_index)
        for s_term, p_node, o_term in triples:
            terms.append(QuotedTripleTerm(subject=s_term, predicate=p_node, object_=o_term))
        return terms

    for row_index in range(len(context.rows_by_tm.get(referenced_tm.identifier, []))):
        triples = _render_tm_row_triples(context, referenced_tm.identifier, row_index)
        for s_term, p_node, o_term in triples:
            terms.append(QuotedTripleTerm(subject=s_term, predicate=p_node, object_=o_term))
    return terms


def _same_logical_source(left: TriplesMap, right: TriplesMap) -> bool:
    return (
        left.logical_source.source == right.logical_source.source
        and left.logical_source.reference_formulation == right.logical_source.reference_formulation
        and left.logical_source.iterator == right.logical_source.iterator
        and left.logical_source.query == right.logical_source.query
    )


def _serialize_triple_line(triple: TripleTerm) -> str:
    subject, predicate, object_ = triple
    return f"{_serialize_term(subject)} {_serialize_term(predicate)} {_serialize_term(object_)} "


def _serialize_term(term: TermLike) -> str:
    if isinstance(term, QuotedTripleTerm):
        return f"<< {_serialize_term(term.subject)} {_serialize_term(term.predicate)} {_serialize_term(term.object_)} >>"
    return term.n3()


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text not in {"", "0", "false", "no", "off", "none", "null"}
