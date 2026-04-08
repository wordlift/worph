from pathlib import Path

from worph.core.config import parse_runtime_config


def test_parse_runtime_config_resolves_relative_file_and_sqlite_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    config_path.write_text(
        "[DataSource1]\n"
        "mappings: mapping.yml\n"
        "file_path: data.json\n"
        "db_url: sqlite:///local.db\n",
        encoding="utf-8",
    )

    runtime = parse_runtime_config(config_path)

    assert runtime.file_path == str((tmp_path / "data.json").resolve())
    assert runtime.db_url == f"sqlite:///{(tmp_path / 'local.db').resolve()}"
