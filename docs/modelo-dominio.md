# Modelo de Domínio, Glossário e Diagrama ER (`docs/modelo-dominio.md`)

Este documento define o modelo de domínio do **DocFlow**, incluindo o glossário da linguagem ubíqua, o Diagrama Entidade-Relacionamento (ER) das **13 entidades centrais**, os contratos de campos estruturados e as máquinas de estado de **`Document`**, **`Media`** e **`Job`**.

---

## 1. Glossário (Linguagem Ubíqua)

| Termo de Negócio | Entidade no Código | Definição no Domínio do DocFlow |
| :--- | :--- | :--- |
| **Instituição (Tenant)** | `Institution` | Escola, secretaria, órgão público ou ONG cadastrada na plataforma SaaS. Unidade raiz de isolamento de dados (`institution_id`, `RN-01`). |
| **Usuário** | `User` | Membro de uma instituição com perfil **`Administrador`** (`ADMIN`) ou **`Funcionário`** (`EMPLOYEE`). Pode estar `ACTIVE` (`Ativo`) ou `INACTIVE` (`Inativo`, `RN-04`). |
| **Mídia** | `Media` | Arquivo de vídeo ou áudio de uma reunião (até **10 GB** e **2h30** de duração, `RN-05`) armazenado no Silo (S3). Versões comprimidas geram um novo registro `Media` apontando para o arquivo original (`source_media_id`, `RN-18`). |
| **Job (Tarefa Assíncrona)** | `Job` | Execução em segundo plano processada pelos workers do Celery (`METADATA_EXTRACTION`, `VIDEO_COMPRESSION`, `TRANSCRIPTION`, `DOCUMENT_GENERATION`, `DOCUMENT_REVIEW`, `DOCUMENT_EXPORT`), com progresso (`0–100%`) e controle de falhas (`RF-09`). |
| **Transcrição** | `Transcript` | Resultado da conversão de uma `Media` em texto em português (`pt-BR`), contendo a lista de falantes e os trechos temporais (`RF-10`). |
| **Falante** | `Speaker` | Pessoa identificada na diarização da transcrição. Nasce com rótulo neutro (`"Falante 1"`, `"Falante 2"`, `RN-17`) e pode ser renomeada por um humano (ex.: `"Marina Carvalho"`), propagando o nome em todos os trechos (`RF-11`). |
| **Trecho de Transcrição** | `TranscriptSegment` | Segmento contínuo de fala dentro de uma `Transcript`, com tempo inicial (`start_ms`), tempo final (`end_ms`), falante (`speaker_id`), texto e índice de confiança (`0.0–1.0`, `RF-12`, `RF-14`). |
| **Modelo de Documento** | `Template` | Estrutura padronizada de documento administrativo (`ATA`, `OFICIO`, `MEMORANDO`, `PRESTACAO_CONTAS`). Pode ser um **modelo padrão do sistema** (`is_system_default = true`, `RF-16`) ou **exclusivo de uma instituição** (`RF-15`). |
| **Versão do Modelo** | `TemplateVersion` | Fotografia imutável de um `Template` publicado, contendo o arquivo base `.docx` e o esquema tipado de campos exigidos. Documentos gerados apontam sempre para uma `TemplateVersion` específica (`RN-12`). |
| **Documento** | `Document` | Documento administrativo gerado ou redigido na instituição. Nasce sempre como `DRAFT` (`Rascunho`, `RN-06`) e passa pelo fluxo de revisão e validação pelo próprio solicitante (`author_id`, `RN-07`). |
| **Versão do Documento** | `DocumentVersion` | Registro imutável de cada revisão do `Document`, guardando o conteúdo textual, os campos extraídos com suas **evidências** na transcrição (`RF-20`), o status de cada campo (`FILLED`, `PENDING`, `AMBIGUOUS`) e os arquivos exportados (`.docx`/`.pdf`). |
| **Evidência de Campo** | *(Valor em `DocumentVersion`)* | Vínculo entre um campo extraído pela IA e o(s) trecho(s) da transcrição (`transcript_segment_id`, `start_ms`, `end_ms`, citação) que comprovam a informação (`RF-20`, `RN-08`). |
| **Registro de Auditoria** | `AuditLog` | Evento imutável (*append-only*, `RN-11`) que registra quem fez o quê e quando na instituição (login, upload, geração, edição, aprovação, devolução, exportação, exclusão). |
| **Consumo / Cota** | `Usage` | Consolidação mensal do consumo da instituição (minutos de áudio transcritos, bytes armazenados no Silo e tokens de LLM consumidos) para controle de limites do plano (`RN-16`; compressão de vídeo é ilimitada e não consome cota, `RN-18`). |

---

## 2. Diagrama Entidade-Relacionamento (ER)

```mermaid
erDiagram
  INSTITUTION ||--o{ USER : "possui"
  INSTITUTION ||--o{ MEDIA : "armazena"
  INSTITUTION ||--o{ TEMPLATE : "personaliza"
  INSTITUTION ||--o{ DOCUMENT : "produz"
  INSTITUTION ||--o{ JOB : "executa"
  INSTITUTION ||--o{ AUDIT_LOG : "registra"
  INSTITUTION ||--o{ USAGE : "contabiliza"

  USER ||--o{ MEDIA : "envia (uploaded_by)"
  USER ||--o{ DOCUMENT : "solicita e valida (author_id)"
  USER ||--o{ AUDIT_LOG : "realiza acao"

  MEDIA ||--o{ MEDIA : "origina comprimida (source_media_id)"
  MEDIA ||--o| TRANSCRIPT : "gera"
  MEDIA ||--o{ JOB : "processada por"

  TRANSCRIPT ||--o{ SPEAKER : "identifica"
  TRANSCRIPT ||--o{ TRANSCRIPT_SEGMENT : "contem"
  SPEAKER ||--o{ TRANSCRIPT_SEGMENT : "fala em"

  TEMPLATE ||--o{ TEMPLATE_VERSION : "possui versoes"
  TEMPLATE_VERSION ||--o{ DOCUMENT : "estrutura"

  DOCUMENT ||--o{ DOCUMENT_VERSION : "historico de versoes"
  DOCUMENT }o--o{ TRANSCRIPT : "baseado em (document_transcripts)"

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

  MEDIA {
    uuid id PK
    uuid institution_id FK
    uuid uploaded_by_id FK
    uuid source_media_id FK "Nullable: aponta p/ original se comprimida (RN-18)"
    string title
    string original_filename
    string content_type
    bigint size_bytes "Max 10 GiB (RN-05)"
    int duration_seconds "Max 9000s / 2h30 (RN-05)"
    string storage_bucket "media-raw | media-processed"
    string storage_key "Prefixo: <institution_id>/<media_id>/..."
    string s3_upload_id "Nullable: Multipart Upload ID"
    string compression_profile "ORIGINAL | LIGHT | HIGH_QUALITY | AUDIO_ONLY"
    string status "UPLOADING | PROCESSING | READY | FAILED | ABORTED | DELETED"
    string error_message
    timestamp expires_at "Calculado pela politica de retencao (RN-14)"
    timestamp created_at
    timestamp updated_at
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
    string language "pt-BR (fixo no MVP)"
    string provider_name "deepgram | assemblyai | google_stt | fake"
    float overall_confidence "0.0 a 1.0"
    int version "Incrementado a cada edicao humana"
    timestamp created_at
    timestamp updated_at
  }

  SPEAKER {
    uuid id PK
    uuid institution_id FK
    uuid transcript_id FK
    string speaker_label "Ex: Falante 1 (RN-17)"
    string display_name "Nome renomeado pelo usuario (RF-11)"
    int speaking_Order
    timestamp created_at
    timestamp updated_at
  }

  TRANSCRIPT_SEGMENT {
    uuid id PK
    uuid institution_id FK
    uuid transcript_id FK
    uuid speaker_id FK
    int segment_index
    int start_ms "Timestamp inicial em ms"
    int end_ms "Timestamp final em ms"
    text content "Texto do trecho (editavel)"
    float confidence "0.0 a 1.0 (RF-14)"
    boolean is_edited
    timestamp updated_at
  }

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
    jsonb fields_schema "Lista de campos: key, label, type, required, rules"
    text body_markdown "Estrutura base ou instrucoes de secao"
    string docx_storage_key "Caminho do template .docx no Silo"
    timestamp published_at
  }

  DOCUMENT {
    uuid id PK
    uuid institution_id FK
    uuid template_version_id FK "Versao exata usada (RN-12)"
    uuid author_id FK "Solicitante e validador do documento (RN-07)"
    string title
    string category "ATA | OFICIO | MEMORANDO | PRESTACAO_CONTAS"
    string status "DRAFT | IN_VALIDATION | APPROVED | RETURNED"
    int current_version_number
    text return_justification "Obrigatorio quando RETURNED (RN-10)"
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
    jsonb extracted_fields "Valores, status (FILLED/PENDING/AMBIGUOUS), confianca e evidencias"
    text rendered_content "Conteudo rico das secoes do documento"
    jsonb ai_review_suggestions "Sugestoes de revisao automatica (RF-22)"
    string docx_storage_key "Arquivo DOCX exportado no Silo"
    string pdf_storage_key "Arquivo PDF exportado no Silo"
    string change_summary "Resumo da alteracao para historico/diff"
    timestamp created_at
  }

  AUDIT_LOG {
    uuid id PK
    uuid institution_id FK
    uuid user_id FK "Nullable em eventos de sistema/falha de login"
    string action "LOGIN | MEDIA_UPLOAD | TRANSCRIPT_EDIT | DOC_GENERATE | DOC_APPROVE | DOC_RETURN | DOC_EXPORT | USER_CHANGE | ..."
    string entity_type "Institution | User | Media | Transcript | Template | Document"
    uuid entity_id
    string summary
    jsonb metadata "Detalhes antes/depois sem dados sensiveis"
    string ip_address
    timestamp created_at "Append-only: sem UPDATE ou DELETE (RN-11)"
  }

  USAGE {
    uuid id PK
    uuid institution_id FK
    string period_month "Formato YYYY-MM (ex: 2026-11)"
    int transcription_minutes_used
    bigint storage_bytes_used
    bigint llm_input_tokens
    bigint llm_output_tokens
    int compression_jobs_count "Apenas informativo — ilimitado no MVP (RN-18)"
    timestamp updated_at
  }
```

---

## 3. Estruturas JSONB Importantes (Campos e Evidências)

### 3.1. Esquema de Campos do Modelo (`TemplateVersion.fields_schema`)
Define quais informações a IA deve extrair da transcrição e quais são obrigatórias para permitir a aprovação (`RN-08`):

```json
[
  {
    "key": "data_reuniao",
    "label": "Data da Reunião",
    "type": "date",
    "required": true,
    "description": "Data em que a reunião ocorreu (DD/MM/AAAA)"
  },
  {
    "key": "participantes",
    "label": "Lista de Participantes",
    "type": "list",
    "required": true,
    "description": "Nomes e cargos dos presentes identificados na reunião"
  },
  {
    "key": "deliberacoes",
    "label": "Deliberações e Encaminhamentos",
    "type": "table",
    "required": true,
    "description": "Decisões tomadas, responsável e prazo acordado"
  }
]
```

### 3.2. Campos Extraídos com Evidência (`DocumentVersion.extracted_fields`)
Garante o cumprimento de `RF-19`, `RF-20` e `RN-08` (a IA nunca inventa valores; tudo que é preenchido aponta para o trecho da transcrição):

```json
{
  "data_reuniao": {
    "value": "2026-11-10",
    "status": "FILLED",
    "confidence": 0.98,
    "evidences": [
      {
        "transcript_id": "8f14e45f-ceea-467f-a8f1-...",
        "segment_id": "3c91a110-12b4-4e89-9a01-...",
        "start_ms": 12400,
        "end_ms": 18900,
        "quote": "Damos início à reunião ordinária do conselho hoje, dia 10 de novembro de 2026."
      }
    ]
  },
  "numero_processo_sei": {
    "value": null,
    "status": "PENDING",
    "confidence": 0.0,
    "evidences": [],
    "missing_reason": "O número do processo administrativo não foi mencionado na gravação."
  }
}
```
> **Regra de Domínio (`RN-08`):** Enquanto existir qualquer campo com `required == true` no `TemplateVersion` cujo `status` em `DocumentVersion.extracted_fields` seja `"PENDING"` ou `"AMBIGUOUS"`, a transição do `Document` para `APPROVED` é bloqueada pelo domínio.

---

## 4. Máquinas de Estado

### 4.1. Máquina de Estados de `Document` (`RF-24`, `RF-25`, `RN-06` a `RN-10`)

```mermaid
stateDiagram-v2
  [*] --> DRAFT : Criado ou gerado pela IA (RN-06)

  DRAFT --> DRAFT : Edição de texto ou regeneração de seção (nova DocumentVersion)
  DRAFT --> IN_VALIDATION : Solicitante envia para validação (RF-25)

  IN_VALIDATION --> APPROVED : Solicitante aprova sem campos obrigatórios pendentes (RN-07, RN-08)
  IN_VALIDATION --> RETURNED : Solicitante devolve com justificativa (RN-10)

  RETURNED --> DRAFT : Solicitante edita documento devolvido
  RETURNED --> IN_VALIDATION : Reenvia após ajustes

  APPROVED --> DRAFT : Edição de aprovado cria nova DocumentVersion em Rascunho (RN-09)
```

### 4.2. Máquina de Estados de `Media` (`RF-05` a `RF-08`, `RN-05`, `RN-14`)

```mermaid
stateDiagram-v2
  [*] --> UPLOADING : Inicia upload multipart (valida <= 10 GB e <= 2h30)

  UPLOADING --> PROCESSING : Conclui envio das partes de 50 MB no Silo
  UPLOADING --> ABORTED : Cancelado pelo usuário ou expirado após 24h

  PROCESSING --> READY : Worker ffprobe valida integridade, áudio e duração <= 2h30 (WK-02)
  PROCESSING --> FAILED : Arquivo corrompido, sem áudio ou duração > 2h30

  READY --> DELETED : Excluída pelo usuário (RF-07) ou política de retenção (RN-14)
```

### 4.3. Máquina de Estados de `Job` (`RF-09`, `RNF-04`, `WK-01`)

```mermaid
stateDiagram-v2
  [*] --> QUEUED : Job criado no banco e publicado no Redis

  QUEUED --> PROCESSING : Worker Celery assume a execução
  QUEUED --> CANCELED : Cancelado pelo usuário antes de iniciar

  PROCESSING --> PROCESSING : Atualiza progresso de 0 a 100 por cento
  PROCESSING --> COMPLETED : Tarefa finalizada com sucesso
  PROCESSING --> QUEUED : Falha transitória (reenfileirado com backoff)
  PROCESSING --> FAILED : Erro definitivo ou limite de tentativas atingido
  PROCESSING --> CANCELED : Cancelado pelo usuário (revoga task e limpa temporários)

  FAILED --> QUEUED : Reprocessamento manual solicitado pelo usuário (RF-09)
```
