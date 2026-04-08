from __future__ import annotations

import os
from pathlib import Path

from .config import RuntimeConfig
from .model import MappingDocument
from .rml_parser import parse_rml
from .yarrrml import parse_yarrrml


YARRRML_EXTENSIONS = {".yml", ".yaml", ".yarrrml"}


def _resolve_mapping_path(mapping_path: str, config: RuntimeConfig) -> str:
    if os.path.exists(mapping_path):
        return mapping_path

    if config.source_path is not None:
        candidate = (config.source_path.parent / Path(mapping_path)).resolve()
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(mapping_path)


def _load_yarrrml_mapping(resolved: str, config: RuntimeConfig) -> MappingDocument:
    return parse_yarrrml(
        resolved,
        file_path_override=config.file_path,
        db_url_override=config.db_url,
    )


def _load_rml_mapping(resolved: str, config: RuntimeConfig) -> MappingDocument:
    return parse_rml(resolved, file_path_override=config.file_path, db_url=config.db_url)


_PARSER_LOADERS = {
    "yarrrml": _load_yarrrml_mapping,
    "rml": _load_rml_mapping,
}


def load_mapping(mapping_path: str, config: RuntimeConfig) -> MappingDocument:
    resolved = _resolve_mapping_path(mapping_path, config)
    ext = os.path.splitext(resolved)[1].lower()
    loader = _PARSER_LOADERS["yarrrml"] if ext in YARRRML_EXTENSIONS else _PARSER_LOADERS["rml"]
    return loader(resolved, config)
