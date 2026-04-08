from __future__ import annotations

import importlib.metadata as importlib_metadata
import importlib.util
import sys
from pathlib import Path

_UPSTREAM_MAIN_MODULE = "_worph_upstream_morph_kgc_main"


def _load_upstream_main():
    module = sys.modules.get(_UPSTREAM_MAIN_MODULE)
    if module is not None:
        return module

    main_path = importlib_metadata.distribution("morph-kgc").locate_file("morph_kgc/__main__.py")
    package_dir = Path(main_path).parent
    spec = importlib.util.spec_from_file_location(
        _UPSTREAM_MAIN_MODULE,
        str(main_path),
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load upstream morph-kgc CLI backend")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_UPSTREAM_MAIN_MODULE] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    upstream = _load_upstream_main()
    if argv is None:
        return int(upstream.main())
    return int(upstream.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
