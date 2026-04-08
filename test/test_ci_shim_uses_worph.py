from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def _in_ci_shim_mode() -> bool:
    for raw_path in sys.path:
        if not raw_path:
            continue
        path = Path(raw_path)
        if path.name == ".ci_shims" and (path / "morph_kgc" / "__init__.py").exists():
            return True
    return False


def test_morph_kgc_shim_uses_worph():
    if not _in_ci_shim_mode():
        pytest.skip("This test requires PYTHONPATH=.ci_shims:src")

    morph_kgc = importlib.import_module("morph_kgc")
    worph = importlib.import_module("worph")

    morph_path = Path(morph_kgc.__file__).resolve()
    assert ".ci_shims" in morph_path.parts
    assert morph_path.name == "__init__.py"
    assert morph_path.parent.name == "morph_kgc"

    assert morph_kgc.materialize is worph.materialize
    assert morph_kgc.materialize_set is worph.materialize_set
    assert morph_kgc.materialize_oxigraph is worph.materialize_oxigraph
