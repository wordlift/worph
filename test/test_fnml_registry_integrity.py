from __future__ import annotations

import pytest

from worph.fnml.built_in_functions import bif, bif_dict
from worph.fnml.registry import build_default_registry


def test_builtin_function_ids_are_unique() -> None:
    function_ids = list(bif_dict.keys())
    assert len(function_ids) == len(set(function_ids))


def test_duplicate_builtin_registration_is_rejected() -> None:
    existing_fun_id = next(iter(bif_dict))

    with pytest.raises(ValueError, match="Duplicate FNML function id registration"):
        @bif(existing_fun_id, value="value")  # pragma: no cover - executed by decorator side effect
        def _duplicate_builtin(value):  # pragma: no cover
            return value


def test_default_registry_contains_expected_core_functions() -> None:
    registry = build_default_registry()

    assert registry.has("equal")
    assert registry.has("http://users.ugent.be/~bjdmeest/function/grel.ttl#math_mod")
    assert registry.has("http://users.ugent.be/~bjdmeest/function/grel.ttl#string_contains")
