"""CLI para geração e verificação do contrato OpenAPI da API DocFlow."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from docflow.main import create_app


def find_repo_root(start: Path | None = None) -> Path:
    """Localiza a raiz do repositório procurando pelo diretório contracts ou .git."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        if (directory / "contracts").is_dir() or (directory / ".git").is_dir():
            return directory

    file_dir = Path(__file__).resolve().parent
    for directory in [file_dir, *file_dir.parents]:
        if (directory / "contracts").is_dir() or (directory / ".git").is_dir():
            return directory

    return current


def get_default_output_path() -> Path:
    """Retorna o caminho padrão para contracts/openapi.json a partir da raiz do repositório."""
    return find_repo_root() / "contracts" / "openapi.json"


def generate_openapi_schema(app: FastAPI | None = None) -> dict[str, Any]:
    """Gera o dicionário de especificação OpenAPI a partir da aplicação FastAPI."""
    target_app = app if app is not None else create_app()
    return target_app.openapi()


def serialize_openapi_schema(schema: dict[str, Any]) -> str:
    """Serializa o schema OpenAPI em formato JSON indentado com 2 espaços e quebra de linha final."""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def check_openapi_schema(output_path: Path, generated_content: str) -> tuple[bool, str]:
    """Compara o conteúdo gerado com o arquivo existente em output_path.

    Retorna (True, "") se idênticos, ou (False, diff_ou_erro) se divergentes ou inexistente.
    """
    if not output_path.exists():
        return False, f"Contract file does not exist: {output_path}"

    try:
        existing_content = output_path.read_text(encoding="utf-8")
    except OSError as err:
        return False, f"Failed to read {output_path}: {err}"

    if existing_content == generated_content:
        return True, ""

    diff = difflib.unified_diff(
        existing_content.splitlines(keepends=True),
        generated_content.splitlines(keepends=True),
        fromfile=f"a/{output_path.name} (existing)",
        tofile=f"b/{output_path.name} (generated)",
    )
    return False, "".join(diff)


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do comando CLI docflow-openapi."""
    parser = argparse.ArgumentParser(
        description="Gera ou valida o contrato OpenAPI (contracts/openapi.json) a partir do app FastAPI.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Caminho do arquivo de saída (default: contracts/openapi.json a partir da raiz do repo).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica se o contrato existente confere com a API sem sobrescrever o arquivo.",
    )

    args = parser.parse_args(argv)

    output_path: Path
    if args.output is not None:
        output_path = args.output.resolve()
    else:
        output_path = get_default_output_path()

    schema = generate_openapi_schema()
    generated_content = serialize_openapi_schema(schema)

    if args.check:
        is_synced, diff_or_error = check_openapi_schema(output_path, generated_content)
        if not is_synced:
            sys.stderr.write(
                f"OpenAPI contract check failed for {output_path}:\n"
                f"{diff_or_error}\n"
                f"Run 'poetry run docflow-openapi' to synchronize the contract.\n"
            )
            return 1
        sys.stdout.write(f"OpenAPI contract is synchronized with {output_path}.\n")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generated_content, encoding="utf-8")
    sys.stdout.write(f"OpenAPI contract successfully written to {output_path}.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
