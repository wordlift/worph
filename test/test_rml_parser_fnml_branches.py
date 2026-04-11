from __future__ import annotations

from rdflib import BNode, Graph, Literal, URIRef

from worph.core.model import FnmlCall
from worph.core.rml_parser import FNML, RML, _parse_term_map, _u


def test_parse_term_map_uses_function_value_lookup():
    graph = Graph()
    node = BNode()
    function_ref = URIRef("urn:fn:ref")
    graph.add((node, _u(FNML, "functionValue"), function_ref))

    function_defs = {
        str(function_ref): FnmlCall(
            function_iri="http://example.com/fn#from-def",
            parameters=[("http://example.com/fn#p", {"reference": "name"})],
        )
    }
    term_map = _parse_term_map(graph, node, function_defs)
    assert term_map.function_call is not None
    assert term_map.function_call.function_iri == "http://example.com/fn#from-def"
    assert term_map.function_call.parameters[0][1] == {"reference": "name"}


def test_parse_term_map_fnml_execution_input_value_map_variants():
    graph = Graph()
    om = BNode()
    execution = URIRef("urn:exec:fnml")
    graph.add((om, _u(FNML, "execution"), execution))
    graph.add((execution, _u(FNML, "function"), URIRef("http://example.com/fn#exec")))

    inp_ref = BNode()
    graph.add((execution, _u(FNML, "input"), inp_ref))
    graph.add((inp_ref, _u(FNML, "parameter"), URIRef("http://example.com/fn#ref")))
    vm_ref = BNode()
    graph.add((inp_ref, _u(FNML, "valueMap"), vm_ref))
    graph.add((vm_ref, _u(RML, "reference"), Literal("name")))

    inp_tpl = BNode()
    graph.add((execution, _u(FNML, "input"), inp_tpl))
    graph.add((inp_tpl, _u(FNML, "parameter"), URIRef("http://example.com/fn#tpl")))
    vm_tpl = BNode()
    graph.add((inp_tpl, _u(FNML, "valueMap"), vm_tpl))
    graph.add((vm_tpl, _u("http://www.w3.org/ns/r2rml#", "template"), Literal("http://example.com/{name}")))

    inp_const = BNode()
    graph.add((execution, _u(FNML, "input"), inp_const))
    graph.add((inp_const, _u(FNML, "parameter"), URIRef("http://example.com/fn#const")))
    vm_const = BNode()
    graph.add((inp_const, _u(FNML, "valueMap"), vm_const))
    graph.add((vm_const, _u("http://www.w3.org/ns/r2rml#", "constant"), Literal("X")))

    inp_nested = BNode()
    graph.add((execution, _u(FNML, "input"), inp_nested))
    graph.add((inp_nested, _u(FNML, "parameter"), URIRef("http://example.com/fn#nested")))
    vm_nested = BNode()
    nested_ref = URIRef("urn:fn:nested")
    graph.add((inp_nested, _u(FNML, "valueMap"), vm_nested))
    graph.add((vm_nested, _u(FNML, "functionValue"), nested_ref))

    term_map = _parse_term_map(
        graph,
        om,
        {str(nested_ref): FnmlCall(function_iri="http://example.com/fn#nested", parameters=[])},
    )
    assert term_map.function_call is not None
    parameters = term_map.function_call.parameters

    def _value_for(name: str):
        matches = [value for param_name, value in parameters if param_name == name]
        assert len(matches) == 1
        return matches[0]

    assert _value_for("http://example.com/fn#ref") == {"reference": "name"}
    assert _value_for("http://example.com/fn#tpl") == {"template": "http://example.com/{name}"}
    assert _value_for("http://example.com/fn#const") == "X"
    nested_value = _value_for("http://example.com/fn#nested")
    assert isinstance(nested_value, FnmlCall)
    assert nested_value.function_iri == "http://example.com/fn#nested"


def test_parse_term_map_rml_function_execution_branch():
    graph = Graph()
    om = BNode()
    execution = URIRef("urn:exec:rml")
    graph.add((om, _u(RML, "functionExecution"), execution))
    graph.add((execution, _u(RML, "function"), URIRef("http://example.com/fn#rml")))

    inp = BNode()
    graph.add((execution, _u(RML, "input"), inp))
    graph.add((inp, _u(RML, "parameter"), URIRef("http://example.com/fn#value")))
    graph.add((inp, _u(RML, "inputValue"), Literal("hello")))

    term_map = _parse_term_map(graph, om, {})
    assert term_map.function_call is not None
    assert term_map.function_call.function_iri == "http://example.com/fn#rml"
    assert term_map.function_call.parameters == [("http://example.com/fn#value", "hello")]


def test_parse_term_map_fnml_execution_fallback_when_function_value_is_unresolved():
    graph = Graph()
    om = BNode()
    graph.add((om, _u(FNML, "functionValue"), URIRef("urn:missing:function")))

    execution = URIRef("urn:exec:fallback")
    graph.add((om, _u(FNML, "execution"), execution))
    graph.add((execution, _u(FNML, "function"), URIRef("http://example.com/fn#fallback")))

    inp = BNode()
    graph.add((execution, _u(FNML, "input"), inp))
    graph.add((inp, _u(FNML, "parameter"), URIRef("http://example.com/fn#value")))
    graph.add((inp, _u(FNML, "inputValue"), Literal("ok")))

    term_map = _parse_term_map(graph, om, {})
    assert term_map.function_call is not None
    assert term_map.function_call.function_iri == "http://example.com/fn#fallback"
    assert term_map.function_call.parameters == [("http://example.com/fn#value", "ok")]


def test_parse_term_map_keeps_resolved_function_value_when_execution_is_also_present():
    graph = Graph()
    om = BNode()
    function_ref = URIRef("urn:fn:resolved")
    graph.add((om, _u(FNML, "functionValue"), function_ref))

    execution = URIRef("urn:exec:should-not-win")
    graph.add((om, _u(FNML, "execution"), execution))
    graph.add((execution, _u(FNML, "function"), URIRef("http://example.com/fn#execution")))
    inp = BNode()
    graph.add((execution, _u(FNML, "input"), inp))
    graph.add((inp, _u(FNML, "parameter"), URIRef("http://example.com/fn#value")))
    graph.add((inp, _u(FNML, "inputValue"), Literal("execution-value")))

    resolved = FnmlCall(
        function_iri="http://example.com/fn#from-def",
        parameters=[("http://example.com/fn#value", {"reference": "name"})],
    )
    term_map = _parse_term_map(graph, om, {str(function_ref): resolved})
    assert term_map.function_call is not None
    assert term_map.function_call.function_iri == "http://example.com/fn#from-def"
    assert term_map.function_call.parameters == [("http://example.com/fn#value", {"reference": "name"})]


def test_parse_term_map_falls_back_to_rml_execution_when_fnml_execution_is_unresolvable():
    graph = Graph()
    om = BNode()

    broken_fnml_execution = URIRef("urn:exec:broken-fnml")
    graph.add((om, _u(FNML, "execution"), broken_fnml_execution))
    # Missing fnml:function on purpose: _parse_fnml_execution should return None.

    rml_execution = URIRef("urn:exec:rml-fallback")
    graph.add((om, _u(RML, "functionExecution"), rml_execution))
    graph.add((rml_execution, _u(RML, "function"), URIRef("http://example.com/fn#rml-fallback")))

    inp = BNode()
    graph.add((rml_execution, _u(RML, "input"), inp))
    graph.add((inp, _u(RML, "parameter"), URIRef("http://example.com/fn#value")))
    graph.add((inp, _u(RML, "inputValue"), Literal("ok")))

    term_map = _parse_term_map(graph, om, {})
    assert term_map.function_call is not None
    assert term_map.function_call.function_iri == "http://example.com/fn#rml-fallback"
    assert term_map.function_call.parameters == [("http://example.com/fn#value", "ok")]
