from __future__ import annotations

from pathlib import Path

from worph.core.model import FnmlCall
from worph.fnml.engine import configure_udfs, evaluate_fnml_call


def test_evaluate_fnml_call_uses_current_default_registry_after_reconfigure(tmp_path: Path) -> None:
    udf_path = tmp_path / "udfs.py"
    udf_path.write_text(
        "\n".join(
            [
                '@udf(fun_id="http://example.com/fn#echo", value="http://example.com/fn#value")',
                "def echo(value):",
                '    return f"echo:{value}"',
            ]
        ),
        encoding="utf-8",
    )
    call = FnmlCall(
        function_iri="http://example.com/fn#echo",
        parameters=[("http://example.com/fn#value", {"reference": "value"})],
    )
    row = {"value": "42"}

    configure_udfs([str(udf_path)])
    assert evaluate_fnml_call(call, lambda ref: row.get(ref)) == "echo:42"

    # Reconfiguration should update the active default registry for subsequent calls.
    configure_udfs([])
    assert evaluate_fnml_call(call, lambda ref: row.get(ref)) is None
