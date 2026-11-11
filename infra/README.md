# Infraestrutura (`infra/`)

Diretório dedicado à infraestrutura como código (IaC), automação de bootstrap e orquestração de contêineres do **DocFlow**.

## Estrutura Planejada

- `terraform/`: módulos (`network`, `compute`, `storage`, `dns`) e ambientes (`staging`, `prod`) com estado remoto no **HCP Terraform** e segredos gerenciados pelo **Infisical**.
- `bootstrap/`: scripts idempotentes de preparação e hardening do servidor on-premise (Docker, Infisical Agent, HCP Terraform Agent, firewall).
- `compose/`: arquivos Docker Compose para desenvolvimento local (`docker-compose.dev.yml`) e ambientes de `staging`/`prod`.

## Regras de Segurança

- **Nenhum segredo** deve ser commitado no repositório ou em arquivos `.tfvars`/`.env`.
- O estado do Terraform (`.tfstate`) reside exclusivamente no **HCP Terraform**.
- As variáveis de ambiente e segredos são injetados via **Infisical**.
