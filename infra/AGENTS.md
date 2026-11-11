# Agent Guidelines for DocFlow Infrastructure (`infra/AGENTS.md`)

Este documento define as regras arquiteturais e convenções obrigatórias para agentes de IA e desenvolvedores ao criar, alterar ou revisar código Terraform e arquivos de infraestrutura dentro de `infra/`.

---

## 1. Resumo da Arquitetura IaC

- **Core Engine**: Terraform `>= 1.8.0`.
- **Estrutura de Diretórios**: os 4 domínios ficam diretamente em `infra/<dominio>/` (sem subpastas `development/` ou `production/`), apontando para o ambiente `prod` no Infisical (`env_slug = "prod"`).
- **Os 4 Domínios de `infra/`**:
  1. **`databases`**: `postgres` (`postgres:16.2-alpine`), `redis` (`redis:7-alpine`), `silo` (`pgsty/silo:latest` + setup de buckets `media-raw`, `media-processed`, `documents` e `loki-data` via `pgsty/mc:latest` com `mcli`). Cria a rede global `shared-network`.
  2. **`apps`**: aplicações desenvolvidas por nós, mapeadas diretamente aos **2 `Dockerfile`s** do projeto:
     - `modules/web` (imagem de `apps/web/Dockerfile`)
     - `modules/server` (imagem única de `apps/server/Dockerfile`, instanciando o contêiner `docflow-api` e os contêineres `docflow-worker-io`, `docflow-worker-cpu` e `docflow-worker-ai` mudando apenas o `command`).
  3. **`tools`**: `pgadmin` e `portainer`.
  4. **`observability`**: `grafana`, `grafana_loki` (storage S3 no Silo) e `grafana_alloy`.
- **Provedores Obrigatórios**:
  - `kreuzwerker/docker` (`~> 3.0.1`): gerencia contêineres, imagens, volumes e redes diretamente no daemon Docker do servidor on-premise (`VM1-ubuntu-2204-cloud-init`). Inclui multiplexação SSH (`ControlMaster=auto`) em `ssh_opts`.
  - `infisical/infisical` (`~> 0.16.0`): busca segredos e configurações em tempo de execução via Universal Auth (`docflow-terraform`) nas pastas `/databases`, `/apps`, `/tools` e `/observability` do ambiente `prod`.
- **Backend de Estado**: **HCP Terraform Cloud** (plano gratuito, organização `DocFlow`) via bloco `cloud {}` em **Local Execution Mode**, com 4 workspaces isolados por domínio (`databases`, `apps`, `tools`, `observability`).
- **Conexão com o Docker**:
  - No servidor / CI runner self-hosted: usa o próprio **socket Unix do Docker** (`TF_VAR_docker_host="unix:///var/run/docker.sock"`).
  - Na máquina local do dev: faz fallback automático para o `docker_ssh_host` armazenado no Infisical (`/databases`), conectando via VPN **Tailscale** (`ssh://ubuntu@100.102.165.104:22`).
- **Exposição Externa (DNS + TLS) vs Acesso Privado**:
  - **Público via Cloudflare Tunnel (`cloudflared`)**: apenas `docflow.gabrieldevops.dev.br` (`docflow-web:80`), `docflow-api.gabrieldevops.dev.br` (`docflow-api:8000`) e `docflow-s3.gabrieldevops.dev.br` (`silo:9000` — somente API S3).
  - **Privado via Tailscale (`100.102.165.104`)**: Silo Console (`:9001`), Grafana (`:3000`), pgAdmin (`:5050`), Portainer (`:9443`) e SSH (`:22`).

---

## 2. Regras Estritas de Desenvolvimento

### 2.1. Segredos e `variables.tf` dos Domínios
1. **NUNCA escreva senhas, chaves de API, tokens ou endpoints sensíveis em código `.tf` ou em arquivos versionados.**
2. O arquivo `<dominio>/variables.tf` deve conter **APENAS**:
   - `infisical_client_id` (`sensitive = true`)
   - `infisical_client_secret` (`sensitive = true`)
   - `infisical_workspace_id`
   - `docker_host` (`default = ""`)
3. Todas as demais variáveis do domínio devem ser lidas via `data "infisical_secrets"` (`env_slug = "prod"`) no `<dominio>/main.tf` e repassadas para o módulo `./modules/env_base`.
4. Ao repassar variáveis cujo nome contenha `secret_key`, `api_key`, `password` ou `token` em blocos HCL, adicione o comentário `# gitleaks:allow` na linha caso o Gitleaks acuse falso positivo (`generic-api-key`).

### 2.2. Padrão de 3 Camadas por Domínio
Todo domínio (`databases`, `apps`, `tools`, `observability`) segue obrigatoriamente a estrutura:
1. **Módulo Atômico (`<dominio>/modules/<servico>`)**:
   - Declara `docker_image` (com `keep_locally = true`), `docker_volume` e `docker_container` (com bloco `lifecycle { ignore_changes = [network_mode, entrypoint, volumes, env] }`).
   - Se precisar injetar arquivos de configuração, coloca o template em `files/` e usa o bloco `upload` com `file()` ou `templatefile()`.
2. **Orquestrador do Domínio (`<dominio>/modules/env_base`)**:
   - Instancia os módulos atômicos do domínio e os conecta à rede `shared-network` (criada como `resource "docker_network" "shared"` em `databases/modules/env_base` e lida via `data "docker_network" "shared"` nos demais domínios).
3. **Root Module do Domínio (`<dominio>/`)**:
   - Configura o bloco `cloud` do HCP Terraform, os providers `docker` e `infisical`, os `data "infisical_secrets"` e instancia `module "<dominio>_env" { source = "./modules/env_base" ... }`.

---

## 3. Regra Obrigatória de Validação (`make check`)

> ⚠️ **REGRA INEGOCIÁVEL PARA AGENTES DE IA E DESENVOLVEDORES:**
> Em **toda e qualquer modificação de infraestrutura** (arquivos `.tf`, `.hcl`, templates em `files/`, `Makefile` ou workflows de CI em `.github/workflows/terraform-ci.yml`), você **DEVE obrigatoriamente** executar o `make check` de `infra/` para validar todas as etapas **ANTES de apresentar o resultado ao usuário**.

```bash
make -C infra check
# (ou, de dentro da pasta infra/: make check)
```

O `make check` executa exatamente as mesmas 6 validações da pipeline de CI (`.github/workflows/terraform-ci.yml`):
1. `make fmt` (`terraform fmt -check -recursive`)
2. `make gitleaks` (`zricethezav/gitleaks:v8.18.2`)
3. `make trufflehog` (`trufflesecurity/trufflehog`)
4. `make tflint` (`ghcr.io/terraform-linters/tflint:v0.54.0 --recursive`)
5. `make trivy` (`aquasec/trivy` — scanners `misconfig,secret`, severidades `CRITICAL,HIGH`)
6. `make checkov` (`bridgecrew/checkov` — frameworks `terraform,secrets`)

Se qualquer uma das 6 verificações falhar, corrija o problema imediatamente e reexecute `make -C infra check` até que todas passem com sucesso antes de finalizar a tarefa.
