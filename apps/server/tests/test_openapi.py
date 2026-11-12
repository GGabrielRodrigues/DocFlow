from __future__ import annotations

import json
from pathlib import Path

import pytest

from docflow.cli.openapi import (
    check_openapi_schema,
    find_repo_root,
    generate_openapi_schema,
    get_default_output_path,
    main,
    serialize_openapi_schema,
)


def test_generate_openapi_schema_contains_required_fields() -> None:
    schema = generate_openapi_schema()
    assert isinstance(schema, dict)
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert schema["info"]["title"] == "DocFlow API"
    assert "/health" in schema["paths"]


def test_serialize_openapi_schema() -> None:
    schema = {"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0.0"}}
    serialized = serialize_openapi_schema(schema)
    assert serialized.endswith("\n")
    assert json.loads(serialized) == schema
    assert '  "openapi": "3.1.0"' in serialized


def test_check_openapi_schema_matches_identical_content(tmp_path: Path) -> None:
    schema = generate_openapi_schema()
    content = serialize_openapi_schema(schema)
    target = tmp_path / "openapi.json"
    target.write_text(content, encoding="utf-8")

    is_synced, diff = check_openapi_schema(target, content)
    assert is_synced is True
    assert diff == ""


def test_check_openapi_schema_fails_when_file_missing(tmp_path: Path) -> None:
    missing_file = tmp_path / "does_not_exist.json"
    is_synced, error = check_openapi_schema(missing_file, '{"test": 1}\n')
    assert is_synced is False
    assert "does not exist" in error


def test_check_openapi_schema_fails_and_produces_diff_when_outdated(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    target.write_text('{"openapi": "3.0.0"}\n', encoding="utf-8")

    is_synced, diff = check_openapi_schema(target, '{"openapi": "3.1.0"}\n')
    assert is_synced is False
    assert '-{"openapi": "3.0.0"}' in diff
    assert '+{"openapi": "3.1.0"}' in diff


def test_main_generates_file_successfully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "subdir" / "openapi.json"
    exit_code = main(["--output", str(target)])
    assert exit_code == 0
    assert target.is_file()

    captured = capsys.readouterr()
    assert "OpenAPI contract successfully written" in captured.out

    content = json.loads(target.read_text(encoding="utf-8"))
    assert content["openapi"] == "3.1.0"


def test_main_check_synchronized_exits_0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "openapi.json"
    assert main(["--output", str(target)]) == 0
    capsys.readouterr()

    exit_code = main(["--output", str(target), "--check"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "OpenAPI contract is synchronized" in captured.out


def test_main_check_divergent_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "openapi.json"
    target.write_text('{"outdated": true}\n', encoding="utf-8")

    exit_code = main(["--output", str(target), "--check"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "OpenAPI contract check failed" in captured.err
    assert "outdated" in captured.err


def test_main_check_missing_file_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "missing.json"

    exit_code = main(["--output", str(target), "--check"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "OpenAPI contract check failed" in captured.err
    assert "does not exist" in captured.err


def test_find_repo_root_and_default_path() -> None:
    repo_root = find_repo_root()
    assert repo_root.is_dir()
    assert (repo_root / "contracts").is_dir() or (repo_root / ".git").is_dir()

    default_path = get_default_output_path()
    assert default_path.name == "openapi.json"
    assert default_path.parent.name == "contracts"
