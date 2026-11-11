# Contrato da API do DocFlow (`contracts/docs/contrato-api.md`)

Este diretório armazena o contrato oficial de comunicação entre o **Backend (`apps/server`)** e o **Frontend (`apps/web`)**, baseado na especificação **OpenAPI 3.1**.

- Durante o desenvolvimento do backend (`BE-23`), o FastAPI exporta automaticamente o esquema `contracts/openapi.json`.
- O frontend gera o seu cliente HTTP e tipos TypeScript (`FE-03`) diretamente a partir de `contracts/openapi.json`.

Abaixo estão definidas as convenções globais e o catálogo de endpoints por módulo de domínio (`DOC-11`).

---

## 1. Convenções Gerais e Versionamento

- **Prefixo de Versão:** Todos os endpoints de negócio utilizam o prefixo `/api/v1` (ex.: `https://api.<dominio>/api/v1/...`).
- **Formato de Dados:**
  - Requisições e respostas utilizam `Content-Type: application/json; charset=utf-8` (respostas de erro utilizam `application/problem+json`).
  - Identificadores (`id`, `institution_id`, etc.) são sempre **UUID v4**.
  - Datas e horários são sempre em **ISO 8601 UTC** (`2026-11-11T14:30:00Z`).
  - Nomes de propriedades JSON utilizam `snake_case` (nativo do FastAPI/Pydantic).
- **Rastreabilidade (`X-Request-ID`):**
  - Toda requisição recebe (ou gera) um cabeçalho `X-Request-ID`, devolvido na resposta e incluído nos logs estruturados e em respostas de erro.

---

## 2. Autenticação e Autorização (JWT + Multi-Tenant)

### 2.1. Envio do Token
Todas as rotas autenticadas exigem o cabeçalho HTTP:
```http
Authorization: Bearer <access_token>
```

### 2.2. Conteúdo do Token (`access_token`)
O `access_token` (JWT assinado, validade padrão de **15 minutos**) carrega no *payload*:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "institution_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "ADMIN",
  "exp": 1794408300
}
```
> **Isolamento Multi-Tenant (`RN-01`):** O `institution_id` **nunca** é lido de parâmetros de URL ou do corpo enviado pelo cliente para filtrar dados; ele é sempre extraído do token JWT autenticado e injetado na sessão do PostgreSQL (RLS).

### 2.3. Perfis de Acesso (`role`)
- `ADMIN` (**Administrador da instituição**): acesso total à instituição, gestão de usuários, modelos institucionais, configurações/cotas, auditoria e todos os fluxos de mídia/documentos.
- `EMPLOYEE` (**Funcionário**): envio de mídias, compressão, transcrição, geração de documentos e **validação (aprovação/devolução) dos documentos que ele próprio solicitou** (`RN-07`).

---

## 3. Convenção de Erros (RFC 9457 — Problem Details)

Qualquer erro retornado pela API (`4xx` ou `5xx`) segue estritamente a **RFC 9457 (`application/problem+json`)**:

```json
{
  "type": "https://api.docflow.com.br/errors/mandatory-fields-pending",
  "title": "Não é possível aprovar documento com campos obrigatórios pendentes",
  "status": 422,
  "detail": "Existem 2 campos obrigatórios marcados como PENDING ou AMBIGUOUS.",
  "instance": "/api/v1/documents/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/approve",
  "request_id": "req_01JCD9X8K3M2",
  "errors": [
    {
      "field": "extracted_fields.data_reuniao",
      "code": "field_pending",
      "message": "O campo obrigatório 'Data da Reunião' está pendente de preenchimento."
    }
  ]
}
```

### Códigos de Status HTTP Padronizados

| Status HTTP | Quando é utilizado |
| :--- | :--- |
| `200 OK` | Leitura, atualização ou ação síncrona concluída. |
| `201 Created` | Criação de recurso síncrono (instituição, usuário, modelo, rascunho). |
| `202 Accepted` | Tarefa assíncrona enfileirada no Celery (devolve o objeto `Job` criado). |
| `204 No Content` | Exclusão ou logout concluído sem corpo de retorno. |
| `400 Bad Request` | JSON malformado ou parâmetros inválidos na requisição. |
| `401 Unauthorized` | Token ausente, expirado ou credenciais de login inválidas. |
| `403 Forbidden` | Usuário autenticado sem permissão (`role` insuficiente ou usuário inativo). |
| `404 Not Found` | Recurso inexistente ou pertencente a outra instituição (nunca revela existência entre tenants). |
| `409 Conflict` | Conflito de estado (ex.: CNPJ/e-mail já cadastrado, editar versão imutável). |
| `413 Content Too Large` | Arquivo declarado acima de 10 GB (`RN-05`). |
| `422 Unprocessable Entity` | Violação de validação ou regra de negócio (ex.: vídeo > 2h30, cota esgotada, aprovar documento com campo obrigatório pendente, devolver sem justificativa). |
| `429 Too Many Requests` | Limite de requisições excedido (*rate limit* em login/recuperação de senha). |
| `500 Internal Server Error` | Falha interna inesperada (detalhes técnicos ficam apenas no log com `request_id`). |

---

## 4. Convenção de Paginação, Ordenação e Filtros

Todos os endpoints de listagem aceitam os seguintes *query parameters*:

- `page`: número da página começando em `1` (padrão: `1`).
- `page_size`: itens por página (padrão: `20`, máximo: `100`).
- `search`: busca textual opcional (título, nome, conteúdo via `tsvector`).
- `sort_by`: campo de ordenação (padrão: `created_at` ou `updated_at`).
- `sort_order`: `asc` ou `desc` (padrão: `desc`).

### Formato de Resposta Paginada
```json
{
  "items": [],
  "total": 54,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

## 5. Catálogo de Endpoints por Contexto (`/api/v1`)

### 5.1. Saúde e Operação (`shared`)
| Método | Rota | Autenticação | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Pública | Verifica se o processo da API está vivo (*liveness*). |
| `GET` | `/ready` | Pública | Verifica conectividade com PostgreSQL, Redis e Silo (*readiness*). |

### 5.2. Autenticação e Identidade (`identity`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/institutions/register` | Pública | Cadastra nova instituição (valida CNPJ) e seu primeiro `ADMIN` (`RF-01`, `RN-02`). |
| `POST` | `/api/v1/auth/login` | Pública | Autentica por e-mail/senha e retorna `access_token` + `refresh_token` (`RF-02`). |
| `POST` | `/api/v1/auth/refresh` | Pública (Token) | Rotaciona o `refresh_token` e emite novo `access_token`. |
| `POST` | `/api/v1/auth/logout` | Autenticado | Revoga o `refresh_token` atual. |
| `POST` | `/api/v1/auth/forgot-password` | Pública | Envia link com token de uso único por e-mail para redefinir senha. |
| `POST` | `/api/v1/auth/reset-password` | Pública | Redefine a senha usando o token recebido por e-mail. |
| `GET` | `/api/v1/auth/me` | Autenticado | Retorna os dados do usuário logado e da sua instituição. |
| `GET` | `/api/v1/institution` | Autenticado | Consulta dados cadastrais, política de retenção, provedores IA habilitados e uso/cotas da instituição. |
| `PATCH` | `/api/v1/institution` | `ADMIN` | Atualiza dados cadastrais da instituição, prazo de retenção e consentimento de IA em nuvem (`RN-14`, `RN-15`). |
| `GET` | `/api/v1/users` | `ADMIN` | Lista usuários da instituição (paginado, filtro por `role` e `status`). |
| `POST` | `/api/v1/users` | `ADMIN` | Cria/convida novo usuário na instituição (`RF-03`). |
| `PATCH` | `/api/v1/users/{user_id}` | `ADMIN` | Edita nome, perfil (`ADMIN`/`EMPLOYEE`) ou status (`ACTIVE`/`INACTIVE`, impedindo desativar o último `ADMIN`, `RN-02`). |

### 5.3. Mídia e Upload Multipart de 10 GB (`media`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/media/uploads/init` | Autenticado | Valida tamanho (`≤ 10 GB`), duração (`≤ 2h30`) e formato; cria `Media` (`UPLOADING`) e inicia Multipart Upload no Silo (`RF-05`, `RN-05`). |
| `POST` | `/api/v1/media/{media_id}/uploads/presign-parts` | Autenticado | Retorna URLs pré-assinadas para o navegador enviar partes de **50 MB** direto ao Silo (`https://s3.<dominio>`). |
| `POST` | `/api/v1/media/{media_id}/uploads/complete` | Autenticado | Finaliza o Multipart Upload com a lista de `{part_number, etag}` e dispara o job `ffprobe` (`WK-02`). |
| `POST` | `/api/v1/media/{media_id}/uploads/abort` | Autenticado | Cancela o upload em andamento e remove partes órfãs no Silo. |
| `GET` | `/api/v1/media` | Autenticado | Lista mídias da instituição (filtros por status, tipo e busca textual, `RF-07`). |
| `GET` | `/api/v1/media/{media_id}` | Autenticado | Retorna detalhes da mídia + URL pré-assinada temporária para player/download. |
| `POST` | `/api/v1/media/{media_id}/compress` | Autenticado | Enfileira job de compressão ilimitada (`LIGHT`, `HIGH_QUALITY`, `AUDIO_ONLY`), gerando nova mídia (`202 Accepted`, `RF-08`, `RN-18`). |
| `DELETE` | `/api/v1/media/{media_id}` | Autenticado | Exclui a mídia do Silo e seus artefatos derivados (`RF-07`, `RF-30`). |

### 5.4. Jobs Assíncronos (`shared` / `jobs`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/jobs` | Autenticado | Lista jobs da instituição (filtro por `status`, `job_type`, `media_id`, `document_id`). |
| `GET` | `/api/v1/jobs/{job_id}` | Autenticado | Consulta estado atual (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELED`) e `progress_percent` (`RF-09`). |
| `GET` | `/api/v1/jobs/{job_id}/events` | Autenticado | Stream Server-Sent Events (SSE) de progresso em tempo real. |
| `POST` | `/api/v1/jobs/{job_id}/cancel` | Autenticado | Cancela job em fila ou em execução. |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Autenticado | Reprocessa um job que falhou (`RF-09`). |

### 5.5. Transcrições e Diarização (`transcription`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/media/{media_id}/transcribe` | Autenticado | Solicita transcrição em `pt-BR` com diarização (retorna `202 Accepted` com o `Job`, `RF-10`). |
| `GET` | `/api/v1/transcripts/{transcript_id}` | Autenticado | Retorna metadados da transcrição e lista de `Speaker`s identificados. |
| `GET` | `/api/v1/transcripts/{transcript_id}/segments` | Autenticado | Lista trechos (`TranscriptSegment`) paginados com `start_ms`, `end_ms`, `speaker_id`, `content` e `confidence` (`RF-12`, `RF-14`). |
| `PATCH` | `/api/v1/transcripts/{transcript_id}/segments/{segment_id}` | Autenticado | Corrige o texto de um trecho ou altera o falante atribuído a ele (`RF-12`). |
| `PATCH` | `/api/v1/transcripts/{transcript_id}/speakers/{speaker_id}` | Autenticado | Renomeia um falante (ex.: `"Falante 1"` → `"Marina"`), propagando em todos os trechos (`RF-11`, `RN-17`). |
| `POST` | `/api/v1/transcripts/{transcript_id}/speakers/merge` | Autenticado | Mescla dois falantes duplicados em um único `speaker_id`. |
| `GET` | `/api/v1/transcripts/{transcript_id}/export` | Autenticado | Exporta a transcrição em `?format=txt|docx|srt|vtt` (`RF-13`). |

### 5.6. Modelos de Documento (`templates`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/templates` | Autenticado | Lista modelos padrão do sistema (`RF-16`) e modelos da instituição (`RF-15`). |
| `GET` | `/api/v1/templates/{template_id}` | Autenticado | Retorna detalhes do modelo e sua `TemplateVersion` ativa (incluindo `fields_schema`). |
| `POST` | `/api/v1/templates` | `ADMIN` | Cria novo modelo institucional e publica sua versão `v1` (`RN-03`). |
| `POST` | `/api/v1/templates/{template_id}/versions` | `ADMIN` | Publica uma nova `TemplateVersion` imutável do modelo (`RN-12`). |
| `PATCH` | `/api/v1/templates/{template_id}` | `ADMIN` | Ativa/desativa modelo ou atualiza metadados básicos. |

### 5.7. Documentos, Geração por IA e Validação (`documents`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents/generate` | Autenticado | Dispara geração assíncrona por IA a partir de `template_id` + `transcript_ids` + `extra_context` (`202 Accepted`, `RF-18`). |
| `POST` | `/api/v1/documents` | Autenticado | Cria documento manualmente em `DRAFT` a partir de um modelo. |
| `GET` | `/api/v1/documents` | Autenticado | Lista documentos da instituição (filtros por `status`, `category`, `search`). |
| `GET` | `/api/v1/documents/{document_id}` | Autenticado | Retorna o documento e sua versão atual (`extracted_fields` com evidências, `rendered_content` e sugestões de revisão). |
| `PUT` | `/api/v1/documents/{document_id}/content` | Autenticado | Atualiza campos pendentes/ambíguos (`RF-19`) ou texto do documento, criando nova `DocumentVersion` (se estava `APPROVED`, volta para `DRAFT`, `RN-09`). |
| `POST` | `/api/v1/documents/{document_id}/regenerate-section` | Autenticado | Solicita à IA a regeneração de uma seção específica (`202 Accepted`, `RF-21`). |
| `POST` | `/api/v1/documents/{document_id}/review` | Autenticado | Executa revisão automática de inconsistências, ortografia e aderência ao modelo (`202 Accepted`, `RF-22`). |
| `POST` | `/api/v1/documents/{document_id}/submit-validation` | Solicitante | Transiciona o documento de `DRAFT`/`RETURNED` para `IN_VALIDATION` (`RF-24`, `RF-25`). |
| `POST` | `/api/v1/documents/{document_id}/approve` | Solicitante (`RN-07`) | Aprova o documento (`IN_VALIDATION` → `APPROVED`), bloqueando se houver campo obrigatório `PENDING` ou `AMBIGUOUS` (`RN-08`). |
| `POST` | `/api/v1/documents/{document_id}/return` | Solicitante (`RN-07`) | Devolve o documento (`IN_VALIDATION` → `RETURNED`) exigindo `justification` obrigatória (`RN-10`). |
| `GET` | `/api/v1/documents/{document_id}/versions` | Autenticado | Lista histórico de versões (`DocumentVersion`) com suporte a comparação e restauração (`RF-26`). |
| `POST` | `/api/v1/documents/{document_id}/versions/{version_number}/restore` | Autenticado | Restaura uma versão anterior como uma nova versão em `DRAFT` (`RF-26`). |
| `POST` | `/api/v1/documents/{document_id}/export` | Autenticado | Gera e retorna URL assinada do arquivo exportado (`format`: `docx` ou `pdf`, `RF-23`). |

### 5.8. Dashboard, Auditoria e LGPD (`audit` / `shared`)
| Método | Rota | Acesso | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/summary` | Autenticado | Indicadores de documentos por status, jobs em processamento, consumo de cotas e atividades recentes (`RF-28`). |
| `GET` | `/api/v1/audit-logs` | `ADMIN` | Consulta paginada da trilha de auditoria imutável (filtros por `user_id`, `action`, `entity_type` e período, `RF-27`). |
| `POST` | `/api/v1/lgpd/data-subject-requests` | `ADMIN` | Solicita exportação ou exclusão de dados pessoais de um titular (`RF-31`). |
