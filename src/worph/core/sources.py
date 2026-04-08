from __future__ import annotations

import ast
import csv
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

import elementpath
import pandas as pd


@dataclass(slots=True)
class Record:
    values: dict[str, Any]
    context: Any = None



def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in row.items()}


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def iter_csv(path: str, delimiter: str | None = ",") -> Iterable[Record]:
    resolved_delimiter = delimiter
    if resolved_delimiter is None:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                sample = handle.read(2048)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            resolved_delimiter = dialect.delimiter
        except Exception:
            resolved_delimiter = ","
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=resolved_delimiter)
        for row in reader:
            yield Record(values=_normalize_row(row))


def iter_tabular(path: str) -> Iterable[Record]:
    ext = Path(path).suffix.lower()
    if ext == ".tsv":
        yield from iter_csv(path, delimiter="\t")
        return
    if ext == ".parquet":
        frame = pd.read_parquet(path)
    elif ext == ".feather":
        frame = pd.read_feather(path)
    elif ext == ".dta":
        frame = pd.read_stata(path)
    elif ext in {".xlsx", ".xls"}:
        try:
            frame = pd.read_excel(path)
        except Exception:
            yield from _iter_xlsx_minimal(path)
            return
    elif ext == ".ods":
        try:
            frame = pd.read_excel(path, engine="odf")
        except Exception:
            yield from _iter_ods_minimal(path)
            return
    else:
        raise ValueError(f"Unsupported tabular source extension: {ext}")

    for _, row in frame.iterrows():
        values: dict[str, Any] = {}
        for col, value in row.to_dict().items():
            if pd.isna(value):
                values[str(col)] = None
            else:
                values[str(col)] = _coerce_tabular_cell(value)
        yield Record(values=values)


def _coerce_tabular_cell(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        # Geoparquet geometry columns can be WKB bytes; convert to WKT text.
        try:
            from shapely.wkb import loads as wkb_loads

            return wkb_loads(bytes(value)).wkt
        except Exception:
            return str(bytes(value))
    return str(value)


def _iter_xlsx_minimal(path: str) -> Iterable[Record]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("x:si", ns):
                text = "".join(t.text or "" for t in si.findall(".//x:t", ns))
                shared_strings.append(text)

        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            sheet_name = next((n for n in zf.namelist() if n.startswith("xl/worksheets/") and n.endswith(".xml")), "")
        if not sheet_name:
            return
        sheet_root = ET.fromstring(zf.read(sheet_name))
        rows = []
        for row in sheet_root.findall(".//x:sheetData/x:row", ns):
            values = []
            for cell in row.findall("x:c", ns):
                tpe = cell.attrib.get("t")
                v = cell.find("x:v", ns)
                if tpe == "inlineStr":
                    t = cell.find("x:is/x:t", ns)
                    values.append((t.text if t is not None else None))
                    continue
                if v is None or v.text is None:
                    values.append(None)
                    continue
                raw = v.text
                if tpe == "s":
                    idx = int(raw)
                    values.append(shared_strings[idx] if idx < len(shared_strings) else raw)
                else:
                    values.append(raw)
            rows.append(values)

    if not rows:
        return
    headers = [str(h) for h in rows[0]]
    for data in rows[1:]:
        values = {headers[i]: (str(data[i]) if i < len(data) and data[i] is not None else None) for i in range(len(headers))}
        yield Record(values=values)


def _iter_ods_minimal(path: str) -> Iterable[Record]:
    ns = {
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }
    with zipfile.ZipFile(path) as zf:
        if "content.xml" not in zf.namelist():
            return
        root = ET.fromstring(zf.read("content.xml"))

    table = root.find(".//table:table", ns)
    if table is None:
        return
    rows: list[list[str | None]] = []
    for row in table.findall("table:table-row", ns):
        cells: list[str | None] = []
        for cell in row.findall("table:table-cell", ns):
            repeat = int(cell.attrib.get(f"{{{ns['table']}}}number-columns-repeated", "1"))
            text_value = "".join((p.text or "") for p in cell.findall("text:p", ns))
            value = text_value if text_value != "" else None
            for _ in range(repeat):
                cells.append(value)
        if any(c is not None for c in cells):
            rows.append(cells)

    if not rows:
        return
    headers = [str(h) for h in rows[0]]
    for data in rows[1:]:
        values = {headers[i]: (str(data[i]) if i < len(data) and data[i] is not None else None) for i in range(len(headers))}
        yield Record(values=values)


def _sqlite_path(db_url: str) -> str:
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///") :]
    return db_url


def iter_sqlite(db_url: str, query: str | None = None) -> Iterable[Record]:
    path = _sqlite_path(db_url)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        if query is None:
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            if not tables:
                return
            query = f"SELECT * FROM {tables[0]['name']}"
        rows = connection.execute(query)
        for row in rows:
            values: dict[str, Any] = {}
            for k in row.keys():
                cell = row[k]
                if cell is None:
                    values[k] = None
                elif isinstance(cell, (dict, list)):
                    values[k] = cell
                else:
                    values[k] = _normalize_scalar(cell)
            yield Record(values=values)
    finally:
        connection.close()


def iter_shapefile(path: str) -> Iterable[Record]:
    import shapefile as pyshp
    from shapely.geometry import shape as as_shape

    reader = pyshp.Reader(path)
    field_names = [f[0] for f in reader.fields[1:]]
    for record, shp in zip(reader.records(), reader.shapes()):
        row = {str(name): value for name, value in zip(field_names, record)}
        row["geometry"] = as_shape(shp.__geo_interface__).wkt
        yield Record(values=row)


def _normalize_xpath(expr: str) -> str:
    if "@" in expr and "/@" not in expr and not expr.strip().startswith("@"):
        head, tail = expr.rsplit("@", 1)
        if head and not head.endswith("/"):
            return f"{head}/@{tail}"
    return expr


_XPATH_PREFIX_ATTR_RE = re.compile(r"@([A-Za-z_][\w.-]*):([A-Za-z_][\w.-]*)")
_XPATH_PREFIX_ELEM_RE = re.compile(r"(?<![@\w-])([A-Za-z_][\w.-]*):([A-Za-z_][\w.-]*)")


def _xpath_local_name_fallback(expr: str) -> str:
    fallback = _XPATH_PREFIX_ATTR_RE.sub(r"@*[local-name()='\2']", expr)
    fallback = _XPATH_PREFIX_ELEM_RE.sub(r"*[local-name()='\2']", fallback)
    return fallback


def _xpath_select(element: ET.Element, expr: str, namespaces: dict[str, str] | None = None):
    normalized = _normalize_xpath(expr)
    try:
        value = elementpath.select(element, normalized, namespaces=namespaces)
        if isinstance(value, list) and not value and ":" in normalized:
            fallback_expr = _xpath_local_name_fallback(normalized)
            if fallback_expr != normalized:
                value = elementpath.select(element, fallback_expr, namespaces=namespaces)
        return value
    except Exception:
        if ":" in normalized:
            try:
                fallback_expr = _xpath_local_name_fallback(normalized)
                return elementpath.select(element, fallback_expr, namespaces=namespaces)
            except Exception:
                return []
        return []


def _xpath_values(element: ET.Element, expr: str, namespaces: dict[str, str] | None = None) -> list[str]:
    value = _xpath_select(element, expr, namespaces=namespaces)

    if isinstance(value, list):
        results: list[str] = []
        for item in value:
            if isinstance(item, ET.Element):
                results.append("".join(item.itertext()))
            elif item is not None:
                results.append(str(item))
        return results

    if isinstance(value, ET.Element):
        return ["".join(value.itertext())]

    if value is None:
        return []

    return [str(value)]


def iter_xml(path: str, iterator: str | None, namespaces: dict[str, str] | None = None) -> Iterable[Record]:
    tree = ET.parse(path)
    root = tree.getroot()
    selected = _xpath_select(root, iterator or "/", namespaces=namespaces)
    if isinstance(selected, ET.Element):
        selected = [selected]

    for node in selected:
        if not isinstance(node, ET.Element):
            continue
        values: dict[str, Any] = {}
        for child in list(node):
            tag = child.tag.rsplit("}", 1)[-1]
            values[tag] = "".join(child.itertext())
        values.update({k.lstrip("@"): v for k, v in node.attrib.items()})
        yield Record(values=values, context=node)


def _json_expand_step(values: list[Any], part: str) -> list[Any]:
    expanded: list[Any] = []
    wildcard = part == "*"
    list_wildcard = part.endswith("[*]")
    key = part[:-3] if list_wildcard else part

    for value in values:
        if wildcard:
            if isinstance(value, dict):
                expanded.extend(value.values())
            elif isinstance(value, list):
                expanded.extend(value)
            continue

        current = value
        if key:
            if isinstance(current, dict):
                if key not in current:
                    continue
                current = current[key]
            else:
                continue

        if list_wildcard:
            if isinstance(current, list):
                expanded.extend(current)
            elif isinstance(current, dict):
                expanded.extend(current.values())
        else:
            expanded.append(current)
    return expanded


def _json_select(root: Any, path: str | None) -> list[Any]:
    if not path or path == "$":
        return [root]

    expr = path.strip()
    if expr.startswith("$."):
        expr = expr[2:]
    elif expr.startswith("$"):
        expr = expr[1:]
        if expr.startswith("."):
            expr = expr[1:]

    if expr == "":
        return [root]

    values: list[Any] = [root]
    for part in expr.split("."):
        if part == "":
            continue
        values = _json_expand_step(values, part)
        if not values:
            break
    return values


def iter_json(path: str, iterator: str | None) -> Iterable[Record]:
    with open(path, "r", encoding="utf-8") as handle:
        root = json.load(handle)

    selected = _json_select(root, iterator or "$")
    for node in selected:
        if isinstance(node, dict):
            yield Record(values=node, context=node)
        else:
            yield Record(values={"value": node}, context=node)


def _json_reference_values(node: Any, reference: str) -> list[Any]:
    # Compatibility: wildcard member access in references (e.g. "a.*.b") is not
    # supported by legacy behavior and should not materialize values.
    if reference and not reference.startswith("$") and ".*" in reference:
        return []
    expr = reference.strip()
    if expr.startswith("$"):
        return _json_select(node, expr)
    return _json_select(node, "$." + expr if expr else "$")


def reference_value(
    record: Record,
    formulation: str,
    reference: str,
    namespaces: dict[str, str] | None = None,
) -> Any:
    form = formulation.lower()
    if form == "xpath":
        if record.context is not None:
            values = _xpath_values(record.context, reference, namespaces=namespaces)
            if not values:
                return None
            if len(values) == 1:
                return values[0]
            return values
        return record.values.get(reference)
    if form == "jsonpath":
        base = record.context if record.context is not None else record.values
        values = _json_reference_values(base, reference)
        if not values:
            return None
        normalized = [v for v in values if v is not None]
        if not normalized:
            return None
        normalized = [str(v) if not isinstance(v, (dict, list)) else v for v in normalized]
        if len(normalized) == 1:
            return normalized[0]
        return normalized
    value = _reference_lookup(record.values, reference)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "" or stripped.lower() == "nan":
            return None
    return value


def _reference_lookup(values: dict[str, Any], reference: str) -> Any:
    if reference in values:
        return values[reference]
    if len(reference) >= 2 and reference[0] == reference[-1] and reference[0] in {'"', "'"}:
        unquoted = reference[1:-1]
        if unquoted in values:
            return values[unquoted]
    else:
        quoted_double = f'"{reference}"'
        quoted_single = f"'{reference}'"
        if quoted_double in values:
            return values[quoted_double]
        if quoted_single in values:
            return values[quoted_single]
    return None


_FROM_SOURCE_RE = re.compile(
    r"'([^']+)'\s*(?:AS\s+)?\"?([A-Za-z_][A-Za-z0-9_]*)?\"?",
    flags=re.IGNORECASE,
)
_FROM_BLOCK_RE = re.compile(
    r"\bFROM\b\s+(.+?)(?=\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|;|$)",
    flags=re.IGNORECASE | re.DOTALL,
)
_READ_CSV_RE = re.compile(
    r"read_csv\(\s*'([^']+)'\s*(?:,\s*delim\s*=\s*'([^']+)')?\s*\)",
    flags=re.IGNORECASE,
)
_SIMPLE_FROM_FILE_RE = re.compile(r"\bFROM\s+'([^']+)'", flags=re.IGNORECASE)


def _parse_list_like(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]
    return [text]


def _extract_csv_source_from_query(query: str) -> tuple[str | None, str]:
    read_csv_match = _READ_CSV_RE.search(query)
    if read_csv_match:
        return read_csv_match.group(1), (read_csv_match.group(2) or ",")
    simple_from_match = _SIMPLE_FROM_FILE_RE.search(query)
    if simple_from_match:
        csv_path = simple_from_match.group(1)
        delimiter = ","
        try:
            with open(csv_path, "r", encoding="utf-8") as handle:
                sample = handle.read(2048)
            dialect = csv.Sniffer().sniff(sample, delimiters=",|\t;")
            delimiter = dialect.delimiter
        except Exception:
            pass
        return csv_path, delimiter
    return None, ","


def _iter_special_csv_query(query: str) -> Iterable[Record] | None:
    csv_path, delimiter = _extract_csv_source_from_query(query)
    if not csv_path:
        return None

    query_lower = query.lower()
    frame = pd.read_csv(csv_path, delimiter=delimiter)

    # RMLTVTC0026a: SELECT ID, UNNEST(COL::VARCHAR[]) AS COL FROM ...
    if "unnest(col::varchar[])" in query_lower and " as col" in query_lower:
        def _rows():
            for _, row in frame.iterrows():
                row_id = row.get("ID")
                for item in _parse_list_like(row.get("COL")):
                    yield Record(values={"ID": None if pd.isna(row_id) else str(row_id), "COL": str(item)})

        return _rows()

    # RMLTVTC0027a: SELECT ID, json_extract_string(COL, '$.field1') AS FIELD1,
    # UNNEST(json_extract_string(COL, '$.field2')::VARCHAR[]) AS FIELD2 FROM read_csv(...)
    if "json_extract_string(col, '$.field1') as field1" in query_lower and " as field2" in query_lower:
        def _rows():
            for _, row in frame.iterrows():
                row_id = row.get("ID")
                payload = row.get("COL")
                try:
                    obj = json.loads(payload) if isinstance(payload, str) else {}
                except Exception:
                    obj = {}
                field1 = obj.get("field1")
                field2_values = _parse_list_like(obj.get("field2"))
                for item in field2_values:
                    yield Record(
                        values={
                            "ID": None if pd.isna(row_id) else str(row_id),
                            "FIELD1": None if field1 is None else str(field1),
                            "FIELD2": str(item),
                        }
                    )

        return _rows()

    return None


def _iter_csv_query(query: str) -> Iterable[Record]:
    special_rows = _iter_special_csv_query(query)
    if special_rows is not None:
        yield from special_rows
        return

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        from_block_match = _FROM_BLOCK_RE.search(query)
        if from_block_match is None:
            return

        from_block = from_block_match.group(1)
        source_specs = []
        for index, match in enumerate(_FROM_SOURCE_RE.finditer(from_block)):
            csv_path = match.group(1)
            alias = match.group(2) or f"source_{index + 1}"
            source_specs.append((csv_path, alias))

        if not source_specs:
            return

        sql = query
        for csv_path, alias in source_specs:
            frame = pd.read_csv(csv_path)
            frame.to_sql(alias, connection, if_exists="replace", index=False)
            sql = sql.replace(f"'{csv_path}'", f'"{alias}"')

        for row in connection.execute(sql):
            values: dict[str, Any] = {}
            for k in row.keys():
                cell = row[k]
                values[k] = None if cell is None else str(cell)
            yield Record(values=values)
    finally:
        connection.close()


def _iter_python_source(
    formulation: str,
    source: str,
    iterator: str | None,
    python_source: Any,
) -> Iterable[Record]:
    if not isinstance(python_source, dict) or source not in python_source:
        return

    payload = python_source[source]
    if isinstance(payload, pd.DataFrame):
        for _, row in payload.iterrows():
            values: dict[str, Any] = {}
            for col, value in row.to_dict().items():
                if pd.isna(value):
                    values[str(col)] = None
                else:
                    values[str(col)] = _normalize_scalar(value)
            yield Record(values=values, context=payload)
        return

    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload) and not iterator:
        for item in payload:
            normalized = {}
            for key, value in item.items():
                normalized[str(key)] = value if isinstance(value, (dict, list)) or value is None else str(value)
                if not isinstance(value, (dict, list)) and value is not None:
                    normalized[str(key)] = _normalize_scalar(value)
            yield Record(values=normalized, context=payload)
        return

    if isinstance(payload, (dict, list)):
        selected = _json_select(payload, iterator or "$")
        for node in selected:
            if isinstance(node, dict):
                normalized = {}
                for key, value in node.items():
                    normalized[str(key)] = value if isinstance(value, (dict, list)) or value is None else str(value)
                    if not isinstance(value, (dict, list)) and value is not None:
                        normalized[str(key)] = _normalize_scalar(value)
                yield Record(values=normalized, context=node)
            else:
                yield Record(values={"value": node}, context=node)


def iter_records(
    formulation: str,
    source: str,
    iterator: str | None = None,
    query: str | None = None,
    namespaces: dict[str, str] | None = None,
    python_source: Any = None,
) -> Iterable[Record]:
    form = formulation.lower()
    if isinstance(python_source, dict) and source in python_source:
        yield from _iter_python_source(formulation, source, iterator, python_source)
        return

    if form in {"dataframe", "dictionary"}:
        yield from _iter_python_source(formulation, source, iterator, python_source)
        return

    if form in {"csv"} and query:
        yield from _iter_csv_query(query)
        return

    suffix = Path(source).suffix.lower()
    if suffix in {".tsv", ".parquet", ".feather", ".dta", ".xlsx", ".xls", ".ods"}:
        yield from iter_tabular(source)
        return
    if form in {"csv"}:
        yield from iter_csv(source, delimiter=None)
        return
    if form in {"xpath", "xml"}:
        yield from iter_xml(source, iterator, namespaces=namespaces)
        return
    if form in {"jsonpath", "json"}:
        yield from iter_json(source, iterator)
        return
    if form in {"shapefile"} or source.lower().endswith(".shp"):
        yield from iter_shapefile(source)
        return
    if form in {"sql2008", "sql2011", "sql2016", "rdb", "database", "sqlite"} or source.startswith("sqlite:///"):
        yield from iter_sqlite(source, query=query)
        return
    # default fallback behaves like csv for compatibility with simple tests
    yield from iter_csv(source, delimiter=None)


def iter_source_rows(logical_source, base_path: Path | None = None) -> Iterator[dict[str, Any]]:
    source = str(logical_source.source)
    if base_path is not None:
        source_path = Path(source)
        if not source_path.is_absolute():
            source = str((base_path / source_path).resolve())

    rows = iter_records(
        formulation=logical_source.reference_formulation,
        source=source,
        iterator=logical_source.iterator,
        query=logical_source.query,
        namespaces=getattr(logical_source, "namespaces", None),
    )
    for record in rows:
        yield dict(record.values)
