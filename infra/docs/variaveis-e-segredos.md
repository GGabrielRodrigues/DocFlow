# Variáveis de Ambiente e Gestão de Segredos no Infisical (`infra/docs/variaveis-e-segredos.md`)

Este documento define a organização do **Infisical** nas 4 pastas correspondentes aos domínios de `infra/` (`/databases`, `/apps`, `/tools`, `/observability`), o contrato estrito dos arquivos `variables.tf` e o inventário de variáveis.

---

## 1. Contrato Estrito de `variables.tf` nos Root Modules

Os arquivos `variables.tf` dos **Root Modules** (`<dominio>/variables.tf`) devem conter **exclusivamente** as variáveis de autenticação no Infisical e a variável opcional de override do socket Docker:

```hcl
# Infisical Universal Auth
variable "infisical_client_id" {
  type        = string
  description = "Client ID for Infisical Universal Auth"
  sensitive   = true
}

variable "infisical_client_secret" {
  type        = string
  description = "Client Secret for Infisical Universal Auth"
  sensitive   = true
}

variable "infisical_workspace_id" {
  type        = string
  description = "Workspace ID (Project ID) in Infisical"
}

# Host Docker Híbrido (vazio = usa docker_ssh_host do Infisical; no servidor = unix:///var/run/docker.sock)
variable "docker_host" {
  type        = string
  description = "Host do daemon Docker. Se vazio, utiliza o valor docker_ssh_host do Infisical"
  default     = ""
}
```

### Template `terraform.tfvars.example`
Em cada domínio (`infra/<dominio>/`), o arquivo `terraform.tfvars.example` versionado contém apenas o esqueleto sem valores:

```hcl
infisical_client_id     = ""
infisical_client_secret = ""
infisical_workspace_id  = ""
```

---

## 2. Estrutura de Pastas no Infisical

No projeto **DocFlow** dentro do Infisical (`env_slug = "prod"`), os segredos são divididos em **4 pastas temáticas** que espelham exatamente os 4 domínios de `infra/`:

```text
Infisical Project: DocFlow (env_slug: prod)
├── /databases       # Postgres, Redis, Silo (S3) + conectividade Docker/GHCR
├── /apps            # Aplicações próprias: docflow-web e docflow-server (API + Workers + IA)
├── /tools           # Ferramentas: pgAdmin e Portainer
└── /observability   # Telemetria: Grafana, Loki e Alloy
```

### Consumo Cross-Domain no `main.tf` do Root Module
Cada Root Module lê a pasta do seu próprio domínio e, quando precisa de credenciais globais (como `docker_ssh_host`, `ghcr_token`, banco ou S3), lê também a pasta `/databases`:

```hcl
data "infisical_secrets" "databases_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/databases"
}

data "infisical_secrets" "apps_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/apps"
}
```

---

## 3. Inventário de Segredos por Pasta no Infisical

> ⚠️ **Importante:** Este inventário documenta apenas os **nomes das chaves** e suas finalidades. Nenhum valor real deve ser escrito neste documento.

### 3.1. Pasta `/databases`
Credenciais do PostgreSQL, Redis, Silo (S3), além das credenciais base do daemon Docker e registro de imagens (GHCR).

| Chave no Infisical (`/databases`) | Descrição | Consumidores |
| :--- | :--- | :--- |
| `docker_ssh_host` | String de conexão SSH para o daemon Docker quando executado fora do servidor (ex.: `ssh -l user -- <ip> docker system dial-stdio`) | Todos os domínios (fallback quando `var.docker_host == ""`) |
| `ghcr_username` | Usuário para pull de imagens privadas no GitHub Container Registry (`ghcr.io`) | Todos os domínios |
| `ghcr_token` | Token (PAT) de leitura de pacotes no GHCR | Todos os domínios |
| `postgres_db` | Nome do banco de dados principal do DocFlow | `databases/modules/postgres`, `apps/modules/server` |
| `postgres_user` | Usuário administrador do PostgreSQL | `databases/modules/postgres`, `apps/modules/server` |
| `postgres_password` | Senha do usuário do PostgreSQL | `databases/modules/postgres`, `apps/modules/server` |
| `redis_password` | Senha de autenticação do Redis (`shared-redis`) | `databases/modules/redis`, `apps/modules/server` |
| `redis_port` | Porta interna do Redis (padrão `6379`) | `databases/modules/redis`, `apps/modules/server` |
| `redis_memory_limit` | Limite de memória RAM do container Redis (em MB) | `databases/modules/redis` |
| `redis_cpu_limit` | Quota de CPU do container Redis | `databases/modules/redis` |
| `silo_root_user` | Usuário root do Silo (fork do MinIO) | `databases/modules/silo` |
| `silo_root_password` | Senha root do Silo | `databases/modules/silo` |
| `silo_docflow_app_user` | Access Key exclusiva da aplicação DocFlow para leitura/escrita nos buckets `media-raw`, `media-processed` e `documents` | `databases/modules/silo`, `apps/modules/server` |
| `silo_docflow_app_password` | Secret Key exclusiva da aplicação DocFlow | `databases/modules/silo`, `apps/modules/server` |
| `silo_public_endpoint` | URL pública HTTPS do Silo via Cloudflare Tunnel (ex.: `https://s3.<dominio>`) usada para assinar URLs de upload multipart | `apps/modules/server` |

### 3.2. Pasta `/apps`
Configurações das nossas duas aplicações (`apps/modules/web` e `apps/modules/server` — incluindo API FastAPI, Workers Celery e provedores de IA em nuvem).

| Chave no Infisical (`/apps`) | Descrição | Consumidores |
| :--- | :--- | :--- |
| `web_image_tag` | Tag da imagem Docker `docflow-web` no GHCR (`apps/web/Dockerfile`) | `apps/modules/web` |
| `server_image_tag` | Tag da imagem Docker única `docflow-server` no GHCR (`apps/server/Dockerfile`) | `apps/modules/server` (API + Workers) |
| `jwt_secret_key` | Chave secreta para assinatura de tokens JWT (acesso e refresh) | `apps/modules/server` |
| `cors_allowed_origins` | Origens permitidas no CORS da API (ex.: `https://app.<dominio>`) | `apps/modules/server` |
| `transcription_provider` | Adaptador ativo de transcrição (`deepgram`, `assemblyai`, `google_stt` ou `fake`) | `apps/modules/server` (`worker-ai`) |
| `deepgram_api_key` | Chave de API do Deepgram (Nova-3) para transcrição com diarização em `pt-BR` | `apps/modules/server` (`worker-ai`) |
| `assemblyai_api_key` | Chave de API do AssemblyAI (provedor reserva de transcrição) | `apps/modules/server` (`worker-ai`) |
| `llm_provider` | Adaptador ativo de LLM (`gemini`, `openai` ou `fake`) | `apps/modules/server` (`worker-ai`) |
| `gemini_api_key` | Chave de API do Google Gemini (`gemini-2.5-flash`) | `apps/modules/server` (`worker-ai`) |
| `openai_api_key` | Chave de API da OpenAI (`gpt-4o-mini`, provedor reserva) | `apps/modules/server` (`worker-ai`) |
| `smtp_host` / `smtp_port` / `smtp_user` / `smtp_password` | Credenciais de envio de e-mails transacionais (recuperação de senha, notificações) | `apps/modules/server` (`worker-io`, `api`) |
| `worker_io_concurrency` | Concorrência do worker da fila `io` | `apps/modules/server` (`worker-io`) |
| `worker_cpu_concurrency` | Concorrência do worker da fila `cpu` (FFmpeg/LibreOffice) | `apps/modules/server` (`worker-cpu`) |
| `worker_ai_concurrency` | Concorrência do worker da fila `ai` | `apps/modules/server` (`worker-ai`) |

### 3.3. Pasta `/tools`
Credenciais administrativas para pgAdmin e Portainer.

| Chave no Infisical (`/tools`) | Descrição | Consumidores |
| :--- | :--- | :--- |
| `pgadmin_default_email` | E-mail de login inicial do pgAdmin 4 | `tools/modules/pgadmin` |
| `pgadmin_default_password` | Senha de login inicial do pgAdmin 4 | `tools/modules/pgadmin` |
| `pgadmin_port` | Porta de acesso ao pgAdmin | `tools/modules/pgadmin` |
| `pgadmin_image_tag` | Tag da imagem do pgAdmin (`dpage/pgadmin4`) | `tools/modules/pgadmin` |
| `portainer_port` | Porta HTTPS do Portainer | `tools/modules/portainer` |
| `portainer_tunnel_port` | Porta do Edge Agent do Portainer | `tools/modules/portainer` |
| `portainer_license_key` | Chave de licença do Portainer (se Business/EE) | `tools/modules/portainer` |

### 3.4. Pasta `/observability`
Credenciais e parâmetros para Grafana, Grafana Loki e Grafana Alloy.

| Chave no Infisical (`/observability`) | Descrição | Consumidores |
| :--- | :--- | :--- |
| `grafana_admin_user` | Usuário administrador do Grafana | `observability/modules/grafana` |
| `grafana_admin_password` | Senha do administrador do Grafana | `observability/modules/grafana` |
| `grafana_port` | Porta do Grafana (ex.: `3000`) | `observability/modules/grafana` |
| `loki_port` | Porta do Grafana Loki (ex.: `3100`) | `observability/modules/grafana_loki` |
| `silo_loki_user` | Access Key do Loki no Silo (S3) | `observability/modules/grafana_loki`, `databases/modules/silo` |
| `silo_loki_password` | Secret Key do Loki no Silo (S3) | `observability/modules/grafana_loki`, `databases/modules/silo` |
| `silo_loki_bucket` | Nome do bucket de logs no Silo (ex.: `docflow-observability-logs`) | `observability/modules/grafana_loki` |
| `silo_internal_url` | Endpoint interno do Silo na `shared-network` (`http://silo:9000`) | `observability/modules/grafana_loki` |
