from __future__ import annotations

from worph.fnml.engine import _resolve_param


def test_template_parameter_keeps_zero_and_false_values() -> None:
    assert (
        _resolve_param(
            {"template": "value={v}"},
            lambda ref: {"v": 0}[ref],
            lambda nested: nested,
        )
        == "value=0"
    )
    assert (
        _resolve_param(
            {"template": "flag={v}"},
            lambda ref: {"v": False}[ref],
            lambda nested: nested,
        )
        == "flag=False"
    )


def test_template_parameter_none_still_resolves_to_empty_text() -> None:
    assert (
        _resolve_param(
            {"template": "value={v}"},
            lambda ref: {"v": None}[ref],
            lambda nested: nested,
        )
        == "value="
    )

