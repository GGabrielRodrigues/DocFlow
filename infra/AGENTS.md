# Agent Guidelines for DocFlow Infrastructure (`infra/AGENTS.md`)

Este documento define as regras arquiteturais e convenções obrigatórias para agentes de IA e desenvolvedores ao criar, alterar ou revisar código Terraform dentro de `infra/`.

---

## 1. Resumo da Arquitetura IaC

- **Core Engine**: Terraform `>= 1.8.0`.
- **Os 4 Domínios de `infra/`**:
  1. **`databases`**: `postgres`, `redis`, `silo` (cria a rede global `shared-network`).
  2. **`apps`**: aplicações desenvolvidas por nós, mapeadas diretamente aos **2 `Dockerfile`s** do projeto:
     - `modules/web` (imagem de `apps/web/Dockerfile`)
     - `modules/server` (imagem única de `apps/server/Dockerfile`, instanciando o contêiner da API FastAPI e os contêineres de Workers do Celery mudando apenas o `command`).
  3. **`tools`**: `pgadmin` e `portainer`.
  4. **`observability`**: `grafana`, `grafana_loki` e `grafana_alloy`.
- **Provedores Obrigatórios**:
  - `kreuzwerker/docker` (`~> 3.0.1`): gerencia contêineres, imagens, volumes e redes diretamente no daemon Docker do servidor on-premise.
  - `infisical/infisical` (`~> 0.16.0`): busca segredos e configurações em tempo de execução via Universal Auth nas pastas `/databases`, `/apps`, `/tools` e `/observability`.
- **Backend de Estado**: **HCP Terraform Cloud** (plano gratuito) via bloco `cloud {}`, com workspaces isolados por domínio.
- **Conexão com o Docker**:
  - No servidor / CI runner self-hosted: usa o próprio **socket Unix do Docker** (`TF_VAR_docker_host="unix:///var/run/docker.sock"`).
  - Na máquina local do dev: faz fallback automático para o `docker_ssh_host` armazenado no Infisical (`/databases`).
- **Exposição Externa (DNS + TLS)**: provida pelo **Cloudflare Tunnel (`cloudflared`)**.

---

## 2. Regras Estritas de Desenvolvimento

### 2.1. Segredos e `variables.tf` dos Domínios
1. **NUNCA escreva senhas, chaves de API, tokens ou endpoints sensíveis em código `.tf` ou em arquivos versionados.**
2. O arquivo `<dominio>/variables.tf` deve conter **APENAS**:
   - `infisical_client_id` (`sensitive = true`)
   - `infisical_client_secret` (`sensitive = true`)
   - `infisical_workspace_id`
   - `docker_host` (`default = ""`)
3. Todas as demais variáveis do domínio devem ser lidas via `data "infisical_secrets"` no `<dominio>/main.tf` e repassadas para o módulo `./modules/env_base`.

### 2.2. Padrão de 3 Camadas por Domínio
Todo domínio (`databases`, `apps`, `tools`, `observability`) segue obrigatoriamente a estrutura:
1. **Módulo Atômico (`<dominio>/modules/<servico>`)**:
   - Declara `docker_image` (com `keep_locally = true`), `docker_volume` e `docker_container` (com bloco `lifecycle { ignore_changes = [network_mode, entrypoint, volumes, env] }`).
   - Se precisar injetar arquivos de configuração, coloca o template em `files/` e usa o bloco `upload` com `file()` ou `templatefile()`.
2. **Orquestrador do Domínio (`<dominio>/modules/env_base`)**:
   - Instancia os módulos atômicos do domínio e os conecta à rede `shared-network` (criada como `resource "docker_network" "shared"` em `databases/modules/env_base` e lida via `data "docker_network" "shared"` nos demais domínios).
3. **Root Module do Domínio (`<dominio>/`)**:
   - Configura o bloco `cloud` do HCP Terraform, os providers `docker` e `infisical`, os `data "infisical_secrets"` e instancia `module "<dominio>_env" { source = "./modules/env_base" ... }`.

### 2.3. Validação Obrigatória
Após qualquer alteração em arquivos `.tf`, execute em `infra/`:
```bash
make check
```
Certifique-se de que `terraform fmt`, `gitleaks`, `trufflehog`, `tflint`, `trivy` e `checkov` passam sem erros.
