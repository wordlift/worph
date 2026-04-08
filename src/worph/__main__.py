from __future__ import annotations

from pathlib import Path
import sys

from worph import materialize
from worph.core.config import parse_runtime_config


_OUTPUT_FORMATS = {
    "N-TRIPLES": "nt",
    "N-QUADS": "nquads",
    "TURTLE": "turtle",
    "RDF/XML": "xml",
    "JSON-LD": "json-ld",
}


def main(argv: list[str] | None = None) -> int:
    cli_args = list(sys.argv[1:] if argv is None else argv)
    if len(cli_args) != 1:
        print("Usage: python -m worph <config.ini>", file=sys.stderr)
        return 2

    config_path = cli_args[0]
    runtime_config = parse_runtime_config(config_path)
    graph = materialize(config_path)

    output_path = Path(runtime_config.output_file or "knowledge-graph.nt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_format = _OUTPUT_FORMATS.get(runtime_config.output_format.upper(), "nt")
    graph.serialize(destination=str(output_path), format=output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
