from __future__ import annotations

import os
from typing import Any

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from .model import FnmlCall, JoinCondition, LogicalSource, MappingDocument, ObjectMapSpec, PredicateObjectMap, TermMap, TriplesMap

RML = "http://w3id.org/rml/"
RML_OLD = "http://semweb.mmlab.be/ns/rml#"
RR = "http://www.w3.org/ns/r2rml#"
FNML = "http://semweb.mmlab.be/ns/fnml#"
FNO = "https://w3id.org/function/ontology#"
QL = "http://semweb.mmlab.be/ns/ql#"
SD = "https://w3id.org/okn/o/sd#"
DEFAULT_GRAPH = URIRef(RML + "defaultGraph")
DEFAULT_GRAPH_RR = URIRef(RR + "defaultGraph")


TYPE_TRIPLES_MAP = URIRef(RR + "TriplesMap")
TYPE_TRIPLES_MAP_OLD = URIRef(RML + "TriplesMap")
TYPE_ASSERTED_TRIPLES_MAP = URIRef(RML + "AssertedTriplesMap")
TYPE_NON_ASSERTED_TRIPLES_MAP = URIRef(RML + "NonAssertedTriplesMap")


def _u(ns: str, term: str) -> URIRef:
    return URIRef(ns + term)


def _object_value(value: Any) -> Any:
    if isinstance(value, Literal):
        return value.toPython()
    if isinstance(value, URIRef):
        return str(value)
    return value


def _first(graph: Graph, subject: Any, predicates: list[URIRef]) -> Any | None:
    for p in predicates:
        value = graph.value(subject, p)
        if value is not None:
            return value
    return None


def _resolve_reference_formulation(raw: Any) -> str:
    if raw is None:
        return "csv"
    text = str(raw)
    if text.startswith(QL):
        text = text[len(QL):]
    if text.startswith(RML):
        text = text[len(RML):]
    if text.startswith(RML_OLD):
        text = text[len(RML_OLD):]
    return text.lower()


def _parse_term_map(graph: Graph, node: Any, function_defs: dict[str, FnmlCall]) -> TermMap:
    constant = _first(graph, node, [_u(RR, "constant"), _u(RML, "constant"), _u(RML_OLD, "constant")])
    template = _first(graph, node, [_u(RR, "template"), _u(RML, "template"), _u(RML_OLD, "template")])
    reference = _first(graph, node, [_u(RML, "reference"), _u(RML_OLD, "reference"), _u(RR, "column")])
    term_type = _first(graph, node, [_u(RR, "termType"), _u(RML, "termType"), _u(RML_OLD, "termType")])
    datatype = _first(graph, node, [_u(RR, "datatype"), _u(RML, "datatype"), _u(RML_OLD, "datatype")])
    language = _first(graph, node, [_u(RR, "language"), _u(RML, "language"), _u(RML_OLD, "language")])
    language_map_node = _first(graph, node, [_u(RR, "languageMap"), _u(RML, "languageMap"), _u(RML_OLD, "languageMap")])

    function_value = _first(graph, node, [_u(FNML, "functionValue")])
    fnml_execution = _first(graph, node, [_u(FNML, "execution")])
    function_execution = _first(graph, node, [_u(RML, "functionExecution"), _u(RML_OLD, "functionExecution")])
    fn_call = None
    if function_value is not None:
        fn_call = function_defs.get(str(function_value))
    if fn_call is None and fnml_execution is not None:
        fn_call = _parse_fnml_execution(graph, fnml_execution, function_defs)
    if fn_call is None and function_execution is not None:
        fn_call = _parse_rml_function_execution(graph, function_execution, function_defs)

    norm_term_type = None
    if term_type is not None:
        term_text = str(term_type)
        if term_text.startswith(RR):
            term_text = term_text[len(RR) :]
        norm_term_type = term_text
    if norm_term_type is None and isinstance(constant, URIRef) and datatype is None and language is None:
        norm_term_type = "IRI"
    if norm_term_type is None and template is not None and datatype is None and language is None:
        template_text = str(template)
        if template_text.startswith(("http://", "https://", "urn:")):
            norm_term_type = "IRI"

    language_map = None
    if language_map_node is not None:
        language_map = _parse_term_map(graph, language_map_node, function_defs)

    return TermMap(
        constant=_object_value(constant),
        template=str(template) if template is not None else None,
        reference=str(reference) if reference is not None else None,
        term_type=norm_term_type,
        datatype=_object_value(datatype),
        language=_object_value(language),
        language_map=language_map,
        function_call=fn_call,
    )


def _parse_rml_function_execution(graph: Graph, execution_node: Any, function_defs: dict[str, FnmlCall]) -> FnmlCall | None:
    function_iri = _first(graph, execution_node, [_u(RML, "function"), _u(RML_OLD, "function")])
    if function_iri is None:
        return None

    parameters = _parse_execution_parameters(
        graph=graph,
        execution_node=execution_node,
        function_defs=function_defs,
        input_predicates=[_u(RML, "input"), _u(RML_OLD, "input")],
        parameter_predicates=[_u(RML, "parameter"), _u(RML_OLD, "parameter")],
        input_value_predicates=[_u(RML, "inputValue"), _u(RML_OLD, "inputValue")],
        input_value_map_predicates=[_u(RML, "inputValueMap"), _u(RML_OLD, "inputValueMap")],
    )

    return FnmlCall(function_iri=str(function_iri), parameters=parameters)


def _parse_fnml_execution(graph: Graph, execution_node: Any, function_defs: dict[str, FnmlCall]) -> FnmlCall | None:
    if str(execution_node) in function_defs:
        return function_defs[str(execution_node)]
    function_iri = _first(graph, execution_node, [_u(FNML, "function"), _u(RML, "function"), _u(RML_OLD, "function")])
    if function_iri is None:
        return None

    parameters = _parse_execution_parameters(
        graph=graph,
        execution_node=execution_node,
        function_defs=function_defs,
        input_predicates=[_u(FNML, "input"), _u(RML, "input"), _u(RML_OLD, "input")],
        parameter_predicates=[_u(FNML, "parameter"), _u(RML, "parameter"), _u(RML_OLD, "parameter")],
        input_value_predicates=[
            _u(FNML, "inputValue"),
            _u(FNML, "value"),
            _u(RML, "inputValue"),
            _u(RML_OLD, "inputValue"),
        ],
        input_value_map_predicates=[
            _u(FNML, "inputValueMap"),
            _u(FNML, "valueMap"),
            _u(RML, "inputValueMap"),
            _u(RML_OLD, "inputValueMap"),
        ],
    )

    return FnmlCall(function_iri=str(function_iri), parameters=parameters)


def _parse_execution_parameters(
    graph: Graph,
    execution_node: Any,
    function_defs: dict[str, FnmlCall],
    input_predicates: list[URIRef],
    parameter_predicates: list[URIRef],
    input_value_predicates: list[URIRef],
    input_value_map_predicates: list[URIRef],
) -> list[tuple[str, Any]]:
    parameters: list[tuple[str, Any]] = []
    input_nodes: list[Any] = []
    for predicate in input_predicates:
        input_nodes += list(graph.objects(execution_node, predicate))
    for inp in input_nodes:
        parameter = _first(graph, inp, parameter_predicates)
        if parameter is None:
            continue
        input_value = _first(graph, inp, input_value_predicates)
        if input_value is not None:
            parameters.append((str(parameter), _object_value(input_value)))
            continue
        ivm = _first(graph, inp, input_value_map_predicates)
        if ivm is None:
            continue
        nested_tm = _parse_term_map(graph, ivm, function_defs)
        if nested_tm.function_call is not None:
            parameters.append((str(parameter), nested_tm.function_call))
        elif nested_tm.reference is not None:
            parameters.append((str(parameter), {"reference": nested_tm.reference}))
        elif nested_tm.template is not None:
            parameters.append((str(parameter), {"template": nested_tm.template}))
        else:
            parameters.append((str(parameter), nested_tm.constant))
    return parameters


def _parse_fnml_calls(graph: Graph) -> dict[str, FnmlCall]:
    calls: dict[str, FnmlCall] = {}

    p_ls = [_u(RML, "logicalSource"), _u(RML_OLD, "logicalSource")]
    p_pom = _u(RR, "predicateObjectMap")
    p_pred_map = _u(RR, "predicateMap")
    p_obj_map = _u(RR, "objectMap")
    p_constant = _u(RR, "constant")

    for subject in graph.subjects(p_pom, None):
        if _first(graph, subject, p_ls) is None:
            continue

        function_iri = None
        params: list[tuple[str, Any]] = []

        for pom in graph.objects(subject, p_pom):
            pm = graph.value(pom, p_pred_map)
            om = graph.value(pom, p_obj_map)
            if pm is None or om is None:
                continue

            pred = graph.value(pm, p_constant)
            obj_ref = graph.value(om, _u(RML, "reference")) or graph.value(om, _u(RML_OLD, "reference"))
            obj_template = graph.value(om, _u(RR, "template"))
            obj_const = graph.value(om, p_constant)
            nested = graph.value(om, _u(FNML, "functionValue"))

            if pred is None:
                continue

            pred_str = str(pred)
            if pred_str == FNO + "executes":
                function_iri = str(obj_const) if obj_const is not None else None
            else:
                if nested is not None:
                    params.append((pred_str, {"fn_ref": str(nested)}))
                elif obj_template is not None:
                    params.append((pred_str, {"template": str(obj_template)}))
                elif obj_ref is not None:
                    params.append((pred_str, {"reference": str(obj_ref)}))
                else:
                    params.append((pred_str, _object_value(obj_const)))

        if function_iri:
            calls[str(subject)] = FnmlCall(function_iri=function_iri, parameters=params)

    # Resolve nested function references recursively.
    resolved: dict[str, FnmlCall] = {}

    def resolve(key: str, stack: set[str]) -> FnmlCall:
        if key in resolved:
            return resolved[key]
        if key in stack:
            return calls[key]
        stack.add(key)
        call = calls[key]
        new_params: list[tuple[str, Any]] = []
        for name, value in call.parameters:
            if isinstance(value, dict) and "fn_ref" in value and value["fn_ref"] in calls:
                new_params.append((name, resolve(value["fn_ref"], stack)))
            else:
                new_params.append((name, value))
        stack.remove(key)
        resolved_call = FnmlCall(function_iri=call.function_iri, parameters=new_params)
        resolved[key] = resolved_call
        return resolved_call

    for key in list(calls.keys()):
        resolve(key, set())

    # Also parse direct fnml:execution nodes used in legacy mappings.
    for execution_node in set(graph.subjects(_u(FNML, "function"), None)):
        key = str(execution_node)
        if key in resolved:
            continue
        parsed = _parse_fnml_execution(graph, execution_node, resolved)
        if parsed is not None:
            resolved[key] = parsed

    return resolved


def _table_name_to_select_all(table_name: Any) -> str:
    text = str(table_name)
    stripped = text.strip()
    if not stripped:
        return "SELECT * FROM "
    if stripped[0] in {'"', "'", "`", "["}:
        return f"SELECT * FROM {stripped}"
    if all(ch.isalnum() or ch == "_" for ch in stripped):
        return f"SELECT * FROM {stripped}"
    escaped = stripped.replace('"', '""')
    return f'SELECT * FROM "{escaped}"'


def parse_rml(path: str, *, file_path_override: str | None = None, db_url: str | None = None) -> MappingDocument:
    graph = Graph()
    graph.parse(path, format="turtle")

    function_defs = _parse_fnml_calls(graph)

    triples_maps: list[TriplesMap] = []
    prefixes = {k: str(v) for k, v in graph.namespaces()}

    tm_candidates = set(graph.subjects(RDF.type, TYPE_TRIPLES_MAP)).union(set(graph.subjects(RDF.type, TYPE_TRIPLES_MAP_OLD)))
    tm_candidates = tm_candidates.union(set(graph.subjects(_u(RML, "logicalSource"), None)))
    tm_candidates = tm_candidates.union(set(graph.subjects(_u(RML_OLD, "logicalSource"), None)))

    for tm in tm_candidates:
        logical_source = _first(graph, tm, [_u(RML, "logicalSource"), _u(RML_OLD, "logicalSource")])
        logical_table = graph.value(tm, _u(RR, "logicalTable"))
        if logical_source is None and logical_table is None:
            continue

        source = None
        iterator = None
        reference_formulation = None
        query = None
        source_from_dataset_spec = False
        if logical_source is not None:
            source = _first(graph, logical_source, [_u(RML, "source"), _u(RML_OLD, "source")])
            if source is not None and not isinstance(source, (Literal, URIRef)):
                dataset_name = _first(graph, source, [_u(SD, "name")])
                if dataset_name is not None:
                    source = dataset_name
                    source_from_dataset_spec = True
            iterator = _first(graph, logical_source, [_u(RML, "iterator"), _u(RML_OLD, "iterator")])
            reference_formulation = _first(
                graph,
                logical_source,
                [_u(RML, "referenceFormulation"), _u(RML_OLD, "referenceFormulation")],
            )
            query = _first(graph, logical_source, [_u(RML, "query"), _u(RML_OLD, "query")])
            table_name = graph.value(logical_source, _u(RR, "tableName"))
            sql_query = graph.value(logical_source, _u(RR, "sqlQuery"))
            sql_version = graph.value(logical_source, _u(RR, "sqlVersion"))
            if sql_query is not None and query is None:
                query = str(sql_query)
            elif table_name is not None and query is None:
                query = _table_name_to_select_all(table_name)
            if source is None and db_url:
                source = db_url
            if reference_formulation is None and (table_name is not None or sql_query is not None or sql_version is not None):
                reference_formulation = "sql2008"
        else:
            source = db_url
            table_name = graph.value(logical_table, _u(RR, "tableName"))
            sql_query = graph.value(logical_table, _u(RR, "sqlQuery"))
            if sql_query is not None:
                query = str(sql_query)
            elif table_name is not None:
                query = _table_name_to_select_all(table_name)
            reference_formulation = "sql2008"

        resolved_formulation = _resolve_reference_formulation(reference_formulation)
        source_value = str(source) if source is not None else ""
        if db_url and not source_value:
            source_value = db_url
        elif file_path_override and resolved_formulation not in {"dataframe", "dictionary"}:
            source_value = file_path_override
        elif (
            source_value
            and not source_from_dataset_spec
            and resolved_formulation not in {"dataframe", "dictionary"}
            and not os.path.isabs(source_value)
            and not source_value.startswith("sqlite:///")
        ):
            source_value = source_value if os.path.exists(source_value) else os.path.join(os.path.dirname(path), source_value)

        ls = LogicalSource(
            source=source_value,
            reference_formulation=resolved_formulation,
            iterator=str(iterator) if iterator is not None else None,
            query=str(query) if query is not None else None,
            namespaces=prefixes,
        )

        subject_node = _first(graph, tm, [_u(RR, "subjectMap"), _u(RML, "subjectMap"), _u(RML_OLD, "subjectMap")])
        if subject_node is None:
            const_subject = _first(graph, tm, [_u(RR, "subject"), _u(RML, "subject"), _u(RML_OLD, "subject")])
            if const_subject is not None:
                subject_map = TermMap(constant=str(const_subject), term_type="iri")
            else:
                continue
        else:
            subject_map = _parse_term_map(graph, subject_node, function_defs)
            if not subject_map.term_type:
                subject_map.term_type = "iri"
        subject_quoted_triples_map = None
        if subject_node is not None:
            quoted_tm = _first(graph, subject_node, [_u(RML, "quotedTriplesMap"), _u(RML_OLD, "quotedTriplesMap")])
            if quoted_tm is not None:
                subject_quoted_triples_map = str(quoted_tm)

        class_iris = []
        if subject_node is not None:
            for cls in graph.objects(subject_node, _u(RR, "class")):
                class_iris.append(str(cls))
            for cls in graph.objects(subject_node, _u(RML, "class")):
                class_iris.append(str(cls))
            for cls in graph.objects(subject_node, _u(RML_OLD, "class")):
                class_iris.append(str(cls))

        po_maps: list[PredicateObjectMap] = []
        has_named_graphs = False
        if subject_node is not None:
            graph_map_node = graph.value(subject_node, _u(RR, "graphMap")) or graph.value(subject_node, _u(RML, "graphMap"))
            if graph_map_node is not None:
                has_named_graphs = True
            graph_node = graph.value(subject_node, _u(RR, "graph")) or graph.value(subject_node, _u(RML, "graph"))
            if graph_node is not None and graph_node not in {DEFAULT_GRAPH, DEFAULT_GRAPH_RR}:
                has_named_graphs = True
        pom_nodes = list(graph.objects(tm, _u(RR, "predicateObjectMap")))
        pom_nodes += list(graph.objects(tm, _u(RML, "predicateObjectMap")))
        pom_nodes += list(graph.objects(tm, _u(RML_OLD, "predicateObjectMap")))
        for pom in pom_nodes:
            graph_map_node = graph.value(pom, _u(RR, "graphMap")) or graph.value(pom, _u(RML, "graphMap"))
            if graph_map_node is not None:
                has_named_graphs = True
            graph_node = graph.value(pom, _u(RR, "graph")) or graph.value(pom, _u(RML, "graph"))
            if graph_node is not None and graph_node not in {DEFAULT_GRAPH, DEFAULT_GRAPH_RR}:
                has_named_graphs = True
            pred_maps: list[TermMap] = []
            obj_maps: list[ObjectMapSpec] = []

            pnodes = list(graph.objects(pom, _u(RR, "predicateMap")))
            pnodes += list(graph.objects(pom, _u(RML, "predicateMap")))
            pnodes += list(graph.objects(pom, _u(RML_OLD, "predicateMap")))
            for pnode in pnodes:
                pred_maps.append(_parse_term_map(graph, pnode, function_defs))

            preds = list(graph.objects(pom, _u(RR, "predicate")))
            preds += list(graph.objects(pom, _u(RML, "predicate")))
            preds += list(graph.objects(pom, _u(RML_OLD, "predicate")))
            for pred in preds:
                pred_maps.append(TermMap(constant=str(pred), term_type="iri"))

            onodes = list(graph.objects(pom, _u(RR, "objectMap")))
            onodes += list(graph.objects(pom, _u(RML, "objectMap")))
            onodes += list(graph.objects(pom, _u(RML_OLD, "objectMap")))
            for onode in onodes:
                parent_tm = graph.value(onode, _u(RR, "parentTriplesMap")) or graph.value(onode, _u(RML, "parentTriplesMap"))
                if parent_tm is not None:
                    conditions: list[JoinCondition] = []
                    jc_nodes = list(graph.objects(onode, _u(RR, "joinCondition")))
                    jc_nodes += list(graph.objects(onode, _u(RML, "joinCondition")))
                    jc_nodes += list(graph.objects(onode, _u(RML_OLD, "joinCondition")))
                    for jc in jc_nodes:
                        child = _first(graph, jc, [_u(RR, "child"), _u(RML, "child"), _u(RML_OLD, "child")])
                        parent = _first(graph, jc, [_u(RR, "parent"), _u(RML, "parent"), _u(RML_OLD, "parent")])
                        if child is not None and parent is not None:
                            conditions.append(JoinCondition(child=str(child), parent=str(parent)))
                    obj_maps.append(ObjectMapSpec(parent_triples_map=str(parent_tm), join_conditions=conditions))
                elif (quoted_tm := (_first(graph, onode, [_u(RML, "quotedTriplesMap"), _u(RML_OLD, "quotedTriplesMap")]))) is not None:
                    obj_maps.append(ObjectMapSpec(quoted_triples_map=str(quoted_tm)))
                else:
                    obj_maps.append(ObjectMapSpec(term_map=_parse_term_map(graph, onode, function_defs)))

            objs = list(graph.objects(pom, _u(RR, "object")))
            objs += list(graph.objects(pom, _u(RML, "object")))
            objs += list(graph.objects(pom, _u(RML_OLD, "object")))
            for obj in objs:
                value = _object_value(obj)
                if isinstance(obj, URIRef):
                    obj_maps.append(ObjectMapSpec(term_map=TermMap(constant=value, term_type="iri")))
                    continue
                if isinstance(obj, Literal):
                    obj_maps.append(
                        ObjectMapSpec(
                            term_map=TermMap(
                                constant=value,
                                term_type="literal",
                                datatype=str(obj.datatype) if obj.datatype is not None else None,
                                language=obj.language,
                            )
                        )
                    )
                    continue
                obj_maps.append(ObjectMapSpec(term_map=TermMap(constant=value, term_type="literal")))

            if pred_maps and obj_maps:
                po_maps.append(PredicateObjectMap(predicate_maps=pred_maps, object_maps=obj_maps))

        triples_maps.append(
            TriplesMap(
                identifier=str(tm),
                logical_source=ls,
                subject_map=subject_map,
                subject_quoted_triples_map=subject_quoted_triples_map,
                asserted=(TYPE_NON_ASSERTED_TRIPLES_MAP not in set(graph.objects(tm, RDF.type))),
                class_iris=class_iris,
                has_named_graphs=has_named_graphs,
                po_maps=po_maps,
            )
        )

    return MappingDocument(prefixes=prefixes, base=None, triples_maps=triples_maps)
