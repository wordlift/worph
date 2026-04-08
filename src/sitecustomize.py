from __future__ import annotations

from pathlib import Path

try:
    from pyoxigraph import Store
except Exception:  # pragma: no cover
    Store = None  # type: ignore[assignment]


if Store is not None:
    _ORIGINAL_BULK_LOAD = Store.bulk_load

    def _patched_bulk_load(self, input, mime_type, **kwargs):
        # pyoxigraph can misinterpret absolute string paths as inline content in some environments.
        if isinstance(input, str):
            candidate = Path(input)
            if candidate.exists():
                with candidate.open("rb") as handle:
                    return _ORIGINAL_BULK_LOAD(self, handle, mime_type, **kwargs)
        return _ORIGINAL_BULK_LOAD(self, input, mime_type, **kwargs)

    Store.bulk_load = _patched_bulk_load


try:
    import pandas as _pd
    from shapely.geometry import shape as _shape
    from shapely.wkb import loads as _wkb_loads
    import shapefile as _pyshp
    import morph_kgc.data_source.data_file as _morph_data_file
except Exception:  # pragma: no cover
    _morph_data_file = None  # type: ignore[assignment]


if _morph_data_file is not None:
    def _read_geoparquet_without_geopandas(rml_rule, references):
        frame = _pd.read_parquet(
            rml_rule["logical_source_value"],
            engine="pyarrow",
            columns=references,
        )
        if "geometry" in frame.columns:
            def _to_wkt(value):
                if value is None:
                    return None
                if isinstance(value, (bytes, bytearray, memoryview)):
                    return _wkb_loads(bytes(value)).wkt
                return str(value)
            frame["geometry"] = frame["geometry"].map(_to_wkt)
        return frame

    def _read_shapefile_without_geopandas(rml_rule, references):
        reader = _pyshp.Reader(rml_rule["logical_source_value"])
        field_names = [f[0] for f in reader.fields[1:]]
        records = []
        for record, shp in zip(reader.records(), reader.shapes()):
            row = {name: value for name, value in zip(field_names, record)}
            row["geometry"] = _shape(shp.__geo_interface__).wkt
            records.append(row)
        frame = _pd.DataFrame(records)
        if references:
            existing = [c for c in references if c in frame.columns]
            if existing:
                frame = frame[existing]
        return frame

    _morph_data_file._read_geoparquet = _read_geoparquet_without_geopandas
    _morph_data_file._read_shapefile = _read_shapefile_without_geopandas
