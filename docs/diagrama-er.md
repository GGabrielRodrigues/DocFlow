# Diagramas Entidade-Relacionamento Detalhados (`docs/diagrama-er.md`)

Para facilitar a leitura direta no GitHub sem precisar de *zoom* ou navegação por setas, o Diagrama Entidade-Relacionamento (ER) completo do **DocFlow** está dividido abaixo nos **3 contextos de domínio** do sistema.

> Voltar para: [`docs/modelo-dominio.md`](./modelo-dominio.md)

---

## 1. Contexto de Identidade, Auditoria e Consumo (`identity`, `audit`)

Reúne a instituição (tenant raiz), seus usuários (`ADMIN` / `EMPLOYEE`), a trilha imutável de auditoria e a contabilização mensal de cotas.

```mermaid
erDiagram
  INSTITUTION ||--o{ USER : "possui"
  INSTITUTION ||--o{ AUDIT_LOG : "registra"
  INSTITUTION ||--o{ USAGE : "contabiliza"
  USER ||--o{ AUDIT_LOG : "executa acao"

  INSTITUTION {
    uuid id PK
    string name
    string institution_type "SCHOOL | PUBLIC_AGENCY | NGO | OTHER"
    string cnpj UK
    string email
    string phone
    string address
    boolean ai_cloud_enabled "RN-15 consentimento IA nuvem"
    int retention_days "RN-14 prazo retencao midias"
    int quota_transcription_minutes "RN-16 limite mensal"
    bigint quota_storage_bytes "RN-16 limite storage"
    timestamp created_at
    timestamp updated_at
  }

  USER {
    uuid id PK
    uuid institution_id FK "RN-01 multi-tenant"
    string name
    string email
    string password_hash "Argon2id"
    string role "ADMIN | EMPLOYEE"
    string status "ACTIVE | INACTIVE"
    timestamp last_login_at
    timestamp created_at
    timestamp updated_at
  }

  AUDIT_LOG {
    uuid id PK
    uuid institution_id FK
    uuid user_id FK "Nullable em falha de login"
    string action "LOGIN | UPLOAD | GENERATE | APPROVE | RETURN | EXPORT"
    string entity_type "Institution | User | Media | Transcript | Document"
    uuid entity_id
    string summary
    jsonb metadata
    string ip_address
    timestamp created_at "Append-only (RN-11)"
  }

  USAGE {
    uuid id PK
    uuid institution_id FK
    string period_month "Formato YYYY-MM"
    int transcription_minutes_used
    bigint storage_bytes_used
    bigint llm_input_tokens
    bigint llm_output_tokens
    int compression_jobs_count "Informativo - ilimitado (RN-18)"
    timestamp updated_at
  }
```

---

## 2. Contexto de Mídia, Jobs e Transcrição (`media`, `transcription`)

Reúne o upload multipart de vídeos/áudios (até 10 GB e 2h30), a fila de jobs assíncronos do Celery e a transcrição com diarização de falantes em português (`pt-BR`).

```mermaid
erDiagram
  MEDIA ||--o{ MEDIA : "origina comprimida (source_media_id)"
  MEDIA ||--o| TRANSCRIPT : "gera"
  MEDIA ||--o{ JOB : "processada por"
  TRANSCRIPT ||--o{ SPEAKER : "identifica"
  TRANSCRIPT ||--o{ TRANSCRIPT_SEGMENT : "contem"
  SPEAKER ||--o{ TRANSCRIPT_SEGMENT : "fala em"

  MEDIA {
    uuid id PK
    uuid institution_id FK
    uuid uploaded_by_id FK
    uuid source_media_id FK "Nullable: original da versao comprimida"
    string title
    string original_filename
    string content_type
    bigint size_bytes "Max 10 GiB (RN-05)"
    int duration_seconds "Max 9000s / 2h30 (RN-05)"
    string storage_bucket "media-raw | media-processed"
    string storage_key "Prefixo: institution_id/media_id/..."
    string s3_upload_id "Multipart Upload ID"
    string compression_profile "ORIGINAL | LIGHT | HIGH_QUALITY | AUDIO_ONLY"
    string status "UPLOADING | PROCESSING | READY | FAILED | ABORTED | DELETED"
    string error_message
    timestamp expires_at "Politica de retencao (RN-14)"
    timestamp created_at
  }

  JOB {
    uuid id PK
    uuid institution_id FK
    uuid created_by_id FK
    uuid media_id FK "Nullable"
    uuid document_id FK "Nullable"
    string job_type "METADATA | COMPRESSION | TRANSCRIPTION | DOC_GEN | DOC_REVIEW | DOC_EXPORT"
    string queue_name "io | cpu | ai"
    string status "QUEUED | PROCESSING | COMPLETED | FAILED | CANCELED"
    int progress_percent "0 a 100"
    int attempts
    string idempotency_key UK
    jsonb payload
    jsonb result_summary
    string error_message
    timestamp started_at
    timestamp finished_at
    timestamp created_at
  }

  TRANSCRIPT {
    uuid id PK
    uuid institution_id FK
    uuid media_id FK
    string language "pt-BR"
    string provider_name "deepgram | assemblyai | google_stt | fake"
    float overall_confidence "0.0 a 1.0"
    int version
    timestamp created_at
    timestamp updated_at
  }

  SPEAKER {
    uuid id PK
    uuid institution_id FK
    uuid transcript_id FK
    string speaker_label "Ex: Falante 1 (RN-17)"
    string display_name "Nome renomeado pelo humano (RF-11)"
    int speaking_order
    timestamp updated_at
  }

  TRANSCRIPT_SEGMENT {
    uuid id PK
    uuid institution_id FK
    uuid transcript_id FK
    uuid speaker_id FK
    int segment_index
    int start_ms "Inicio em ms"
    int end_ms "Fim em ms"
    text content "Texto editavel"
    float confidence "0.0 a 1.0 (RF-14)"
    boolean is_edited
    timestamp updated_at
  }
```

---

## 3. Contexto de Modelos e Documentos (`templates`, `documents`)

Reúne o catálogo versionado de modelos (`Template` e `TemplateVersion`) e os documentos gerados pela IA, suas versões imutáveis com evidências e arquivos exportados (`.docx`/`.pdf`).

```mermaid
erDiagram
  TEMPLATE ||--o{ TEMPLATE_VERSION : "possui versoes"
  TEMPLATE_VERSION ||--o{ DOCUMENT : "estrutura (RN-12)"
  DOCUMENT ||--o{ DOCUMENT_VERSION : "historico de versoes"
  DOCUMENT }o--o{ TRANSCRIPT : "baseado em (document_transcripts)"

  TEMPLATE {
    uuid id PK
    uuid institution_id FK "Nullable se is_system_default = true"
    string name
    string category "ATA | OFICIO | MEMORANDO | PRESTACAO_CONTAS"
    string description
    boolean is_system_default "RF-16 modelo padrao"
    boolean is_active
    int current_version_number
    timestamp created_at
    timestamp updated_at
  }

  TEMPLATE_VERSION {
    uuid id PK
    uuid institution_id FK "Nullable se modelo do sistema"
    uuid template_id FK
    int version_number "Imutavel apos publicacao (RN-12)"
    jsonb fields_schema "Campos tipados e obrigatoriedade"
    text body_markdown "Estrutura base das secoes"
    string docx_storage_key "Template .docx no Silo"
    timestamp published_at
  }

  DOCUMENT {
    uuid id PK
    uuid institution_id FK
    uuid template_version_id FK "Versao exata usada (RN-12)"
    uuid author_id FK "Solicitante e validador (RN-07)"
    string title
    string category "ATA | OFICIO | MEMORANDO | PRESTACAO_CONTAS"
    string status "DRAFT | IN_VALIDATION | APPROVED | RETURNED"
    int current_version_number
    text return_justification "Obrigatorio se RETURNED (RN-10)"
    timestamp approved_at
    timestamp created_at
    timestamp updated_at
  }

  DOCUMENT_VERSION {
    uuid id PK
    uuid institution_id FK
    uuid document_id FK
    uuid created_by_id FK
    int version_number
    jsonb extracted_fields "Valor, status (FILLED/PENDING/AMBIGUOUS), confianca e evidencias"
    text rendered_content "Conteudo textual das secoes"
    jsonb ai_review_suggestions "Sugestoes de revisao (RF-22)"
    string docx_storage_key "DOCX exportado no Silo"
    string pdf_storage_key "PDF exportado no Silo"
    string change_summary "Resumo da versao"
    timestamp created_at
  }
```
