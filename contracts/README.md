# Contratos da API (`contracts/`)

Diretório responsável por armazenar os contratos compartilhados entre o **Backend (`apps/server`)** e o **Frontend (`apps/web`)** do **DocFlow**.

---

## Documentação do Módulo (`contracts/docs/`)

- 📄 **[`docs/contrato-api.md`](./docs/contrato-api.md)** — Convenções globais da API REST (`/api/v1`), autenticação JWT multi-tenant, padrão de erros (RFC 9457), paginação e catálogo completo de endpoints por contexto de negócio.

---

## Fluxo de Geração e Consumo do `openapi.json`

1. **Exportação pelo Backend (`apps/server`):**
   O FastAPI gera automaticamente a especificação OpenAPI 3.1 no arquivo `contracts/openapi.json` (validado em CI para garantir que nunca fique desatualizado em relação ao código Python).
2. **Geração de Cliente Tipado no Frontend (`apps/web`):**
   O frontend consome `contracts/openapi.json` via `openapi-typescript` / `orval` para gerar os tipos TypeScript e os *hooks* de requisição, garantindo sincronia de tipos de ponta a ponta.
