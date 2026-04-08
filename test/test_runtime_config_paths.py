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


def test_parse_runtime_config_keeps_existing_repo_relative_sqlite_path(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    config_dir = repo / "examples" / "postgres"
    config_dir.mkdir(parents=True)
    db_path = repo / "examples" / "postgres" / "example.db"
    db_path.write_text("", encoding="utf-8")
    config_path = config_dir / "config.ini"
    config_path.write_text(
        "[DataSource1]\n"
        "mappings: mapping.ttl\n"
        "db_url: sqlite:///examples/postgres/example.db\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    runtime = parse_runtime_config(config_path)

    assert runtime.db_url == f"sqlite:///{db_path.resolve()}"


def test_parse_runtime_config_keeps_existing_repo_relative_file_path(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    config_dir = repo / "examples" / "s3_parquet"
    config_dir.mkdir(parents=True)
    data_path = repo / "examples" / "s3_parquet" / "data.parquet"
    data_path.write_text("", encoding="utf-8")
    config_path = config_dir / "config.ini"
    config_path.write_text(
        "[DataSource1]\n"
        "mappings: mapping.ttl\n"
        "file_path: examples/s3_parquet/data.parquet\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    runtime = parse_runtime_config(config_path)

    assert runtime.file_path == str(data_path.resolve())


def test_parse_runtime_config_path_precedence_prefers_existing_cwd_file_path(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    config_dir = repo / "configs"
    config_dir.mkdir(parents=True)
    cwd_path = repo / "shared.csv"
    config_relative_path = config_dir / "shared.csv"
    cwd_path.write_text("cwd", encoding="utf-8")
    config_relative_path.write_text("config-dir", encoding="utf-8")
    config_path = config_dir / "config.ini"
    config_path.write_text(
        "[DataSource1]\n"
        "mappings: mapping.ttl\n"
        "file_path: shared.csv\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    runtime = parse_runtime_config(config_path)

    assert runtime.file_path == str(cwd_path.resolve())


def test_parse_runtime_config_path_precedence_prefers_existing_cwd_sqlite_path(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    config_dir = repo / "configs"
    config_dir.mkdir(parents=True)
    cwd_db = repo / "shared.db"
    config_db = config_dir / "shared.db"
    cwd_db.write_text("", encoding="utf-8")
    config_db.write_text("", encoding="utf-8")
    config_path = config_dir / "config.ini"
    config_path.write_text(
        "[DataSource1]\n"
        "mappings: mapping.ttl\n"
        "db_url: sqlite:///shared.db\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    runtime = parse_runtime_config(config_path)

    assert runtime.db_url == f"sqlite:///{cwd_db.resolve()}"
