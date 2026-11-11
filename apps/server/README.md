# DocFlow Server (`apps/server`)

Monolito modular em **Python 3.12+** responsável pela **API HTTP (FastAPI)** e pelos **workers assíncronos (Celery)** do DocFlow.

## Arquitetura Planejada

O código-fonte em `apps/server` organiza-se por módulos de domínio:
- `identity`: instituições (multi-tenant), usuários, autenticação e RBAC
- `media`: upload multipart no S3/MinIO, metadados e compressão de mídia
- `transcription`: pipeline de transcrição com diarização de falantes (`TranscriptionProvider`)
- `templates`: catálogo e versionamento de modelos de documentos
- `documents`: geração assistida por IA (`LLMProvider`), revisão, fluxo de validação e exportação (DOCX/PDF)
- `audit`: trilha de auditoria imutável (append-only)
- `shared`: configurações (`pydantic-settings`), banco de dados (SQLAlchemy 2 + Alembic), filas e utilitários transversais

Cada módulo segue a separação em camadas: `domain`, `application`, `infrastructure` e `api`.

> Consulte o backlog em [`docs/backlog-issues.md`](../../docs/backlog-issues.md) (issues `BE-*` e `WK-*`) para acompanhar a implementação.
