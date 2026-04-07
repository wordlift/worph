from __future__ import annotations

import re
from typing import Any

from worph.fnml.engine import evaluate_fnml_call

from .model import TermMap
from .sources import Record, reference_value

_TEMPLATE_PATTERN = re.compile(r"\{([^{}]+)\}")
_ESC_L = "\uFFF0"
_ESC_R = "\uFFF1"



def render_term_map(
    term_map: TermMap,
    record: Record,
    formulation: str,
    namespaces: dict[str, str] | None = None,
) -> Any | None:
    if term_map.constant is not None:
        return term_map.constant

    if term_map.function_call is not None:
        return evaluate_fnml_call(
            term_map.function_call,
            lambda ref: reference_value(record, formulation, ref, namespaces=namespaces),
        )

    if term_map.template is not None:
        return _render_template(term_map.template, record, formulation, namespaces=namespaces)

    if term_map.reference is not None:
        return reference_value(record, formulation, term_map.reference, namespaces=namespaces)

    return None


def is_probable_iri(value: str) -> bool:
    return value.startswith(("http://", "https://", "urn:"))


def _render_template(
    template: str,
    record: Record,
    formulation: str,
    namespaces: dict[str, str] | None = None,
) -> Any:
    expanded = _expand_template_values(template, record, formulation, namespaces=namespaces)
    if len(expanded) == 1:
        return expanded[0]
    return expanded


def _expand_template_values(
    template: str,
    record: Record,
    formulation: str,
    namespaces: dict[str, str] | None = None,
) -> list[str]:
    template = template.replace("\\{", _ESC_L).replace("\\}", _ESC_R)
    match = _TEMPLATE_PATTERN.search(template)
    if not match:
        return [template.replace(_ESC_L, "{").replace(_ESC_R, "}")]

    token = match.group(1)
    value = reference_value(record, formulation, token, namespaces=namespaces)
    values = value if isinstance(value, list) else [value]
    if not values:
        return []

    start, end = match.span()
    head = template[:start]
    tail = template[end:]

    expanded: list[str] = []
    for item in values:
        if item is None:
            continue
        replacement = "" if item is None else str(item)
        expanded.extend(
            _expand_template_values(
                head + replacement + tail,
                record,
                formulation,
                namespaces=namespaces,
            )
        )
    return expanded
