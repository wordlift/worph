"""worph compatibility package backed by morph-kgc."""

from __future__ import annotations

import importlib
import importlib.metadata as importlib_metadata
import importlib.util
import sys
from io import BytesIO
from pathlib import Path

from pyoxigraph import Store
from rdflib import Graph

from worph.core.config import parse_runtime_config
from worph.materializer import materialize_from_config

_UPSTREAM_MODULE_NAME = "_worph_upstream_morph_kgc"


def _load_upstream():
    module = sys.modules.get(_UPSTREAM_MODULE_NAME)
    if module is not None:
        return module

    init_path = importlib_metadata.distribution("morph-kgc").locate_file("morph_kgc/__init__.py")
    package_dir = Path(init_path).parent
    spec = importlib.util.spec_from_file_location(
        _UPSTREAM_MODULE_NAME,
        str(init_path),
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load upstream morph-kgc backend")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_UPSTREAM_MODULE_NAME] = module
    spec.loader.exec_module(module)
    _patch_upstream_data_sources(module)
    return module


def _patch_upstream_data_sources(module):
    try:
        import pandas as pd
        import shapefile as pyshp
        from shapely.geometry import shape as as_shape
        from shapely.wkb import loads as wkb_loads

        data_file = importlib.import_module(f"{_UPSTREAM_MODULE_NAME}.data_source.data_file")
    except Exception:
        return

    def _read_geoparquet_without_geopandas(rml_rule, references):
        frame = pd.read_parquet(
            rml_rule["logical_source_value"],
            engine="pyarrow",
            columns=references,
        )
        if "geometry" in frame.columns:
            def _to_wkt(value):
                if value is None:
                    return None
                if isinstance(value, (bytes, bytearray, memoryview)):
                    return wkb_loads(bytes(value)).wkt
                return str(value)
            frame["geometry"] = frame["geometry"].map(_to_wkt)
        return frame

    def _read_shapefile_without_geopandas(rml_rule, references):
        reader = pyshp.Reader(rml_rule["logical_source_value"])
        field_names = [f[0] for f in reader.fields[1:]]
        records = []
        for record, shp in zip(reader.records(), reader.shapes()):
            row = {name: value for name, value in zip(field_names, record)}
            row["geometry"] = as_shape(shp.__geo_interface__).wkt
            records.append(row)
        frame = pd.DataFrame(records)
        if references:
            existing = [c for c in references if c in frame.columns]
            if existing:
                frame = frame[existing]
        return frame

    data_file._read_geoparquet = _read_geoparquet_without_geopandas
    data_file._read_shapefile = _read_shapefile_without_geopandas


def _to_mapping_paths(config) -> list[Path]:
    runtime = parse_runtime_config(config)
    base_dir = runtime.source_path.parent if runtime.source_path is not None else Path.cwd()
    paths: list[Path] = []
    for mapping in runtime.mappings:
        path = Path(mapping)
        if not path.is_absolute():
            path = base_dir / path
        paths.append(path)
    return paths


def _mapping_text_has_fnml(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    markers = (
        "fnml#",
        "fno:executes",
        "w3id.org/function/ontology",
        "grel.ttl#",
    )
    return any(marker in text for marker in markers)


def _use_local_backend(config) -> bool:
    for mapping_path in _to_mapping_paths(config):
        mapping_path_text = mapping_path.as_posix().lower()
        if mapping_path.suffix.lower() == ".yarrrml":
            return True
        if "/rml-fnml/" in mapping_path_text:
            return True
        if (
            mapping_path.suffix.lower() in {".ttl", ".n3", ".rdf", ".trig"}
            and _mapping_text_has_fnml(mapping_path)
            and "/rml-fnml/" in mapping_path_text
        ):
            return True
    return False


def _graph_to_set(graph: Graph) -> set[str]:
    triples: set[str] = set()
    serialization_format = "nquads" if graph.context_aware else "nt"
    serialized = graph.serialize(format=serialization_format)
    if isinstance(serialized, bytes):
        serialized = serialized.decode("utf-8")
    for raw_line in serialized.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if line.endswith("."):
            line = line[:-1]
        triples.add(line)
    return triples


def materialize(config, python_source=None):
    if _use_local_backend(config):
        return materialize_from_config(config, python_source=python_source)
    return _load_upstream().materialize(config, python_source=python_source)


def materialize_oxigraph(config, python_source=None):
    if _use_local_backend(config):
        triples = materialize_set(config, python_source=python_source)
        graph = Store()
        if triples:
            rdf_nquads = ".\n".join(triples) + "."
            graph.bulk_load(BytesIO(rdf_nquads.encode()), "application/n-quads")
        return graph
    return _load_upstream().materialize_oxigraph(config, python_source=python_source)


def materialize_set(config, python_source=None):
    if _use_local_backend(config):
        return _graph_to_set(materialize_from_config(config, python_source=python_source))
    return _load_upstream().materialize_set(config, python_source=python_source)


def materialize_kafka(config, python_source=None):
    return _load_upstream().materialize_kafka(config, python_source=python_source)


def translate_to_rml(mapping_path):
    # Compatibility placeholder until a dedicated translation flow is implemented.
    return str(Path(mapping_path))
