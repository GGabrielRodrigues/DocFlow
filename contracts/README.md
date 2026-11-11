# Contratos da API (`contracts/`)

Diretório destinado aos contratos compartilhados entre o backend (`apps/server`) e o frontend (`apps/web`), incluindo a especificação **OpenAPI** (`openapi.json` / `openapi.yaml`).

## Fluxo de Trabalho

1. A especificação inicial e evoluções de contrato são documentadas e exportadas pelo backend FastAPI (`apps/server`).
2. O arquivo `openapi.json` versionado neste diretório serve como fonte única de verdade para a geração do cliente HTTP tipado no frontend (`apps/web`).
