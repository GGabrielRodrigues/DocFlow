# DocFlow — Automatizador de Atas e Documentos Administrativos

O **DocFlow** é uma plataforma SaaS multi-instituição voltada para escolas e instituições públicas ou privadas, projetada para simplificar, padronizar e automatizar a criação, transcrição de reuniões, geração assistida por IA, validação e rastreabilidade de documentos institucionais — como **Atas**, **Ofícios** e **Prestações de contas**.

---

## Estrutura do Monorepo

O repositório está organizado como um monorepo contendo aplicações, contratos, infraestrutura e documentação:

```text
.
├── apps/
│   ├── web/         # Frontend em React 19 + TypeScript + Vite + Tailwind CSS v4
│   └── server/      # Backend modular em Python 3.12+ (FastAPI) + Workers (Celery)
├── contracts/       # Contratos compartilhados da API (especificação OpenAPI)
├── docs/            # Documentação de produto, requisitos, ADRs, arquitetura e backlog
├── infra/           # Infraestrutura como Código (Terraform, Docker Compose, scripts de bootstrap)
├── .github/         # Templates de Issues, Pull Requests e workflows de CI/CD
├── .editorconfig    # Padronização de formatação entre editores
├── .gitignore       # Regras globais de arquivos ignorados pelo Git
└── CONTRIBUTING.md  # Guia de contribuição, fluxo de branches, commits e PRs
```

### Descrição dos Módulos

| Diretório | Responsabilidade | Tecnologias Principais |
| :--- | :--- | :--- |
| [`apps/web`](./apps/web) | Interface web para usuários e administradores (gestão de mídias, editor de transcrições, geração/validação de documentos e auditoria). Contém o protótipo funcional demonstrativo. | React 19, TypeScript 5.7, Vite 8, Tailwind CSS v4 |
| [`apps/server`](./apps/server) | Monolito modular com API HTTP e processamento assíncrono em background (extração de áudio/vídeo com FFmpeg, transcrição com diarização e geração/revisão documental por LLM). | Python 3.12+, FastAPI, Celery, SQLAlchemy 2, PostgreSQL, Redis |
| [`contracts`](./contracts) | Especificações OpenAPI (`openapi.json`) exportadas pelo backend e utilizadas para geração de clientes tipados no frontend. | OpenAPI 3.1 |
| [`infra`](./infra) | Provisionamento e operação do servidor on-premise, object storage S3-compatível (Silo, fork do MinIO), banco de dados, proxy reverso e gestão de segredos. | Terraform (HCP Terraform), Infisical, Docker Compose, Silo |
| [`docs`](./docs) | Requisitos funcionais/não-funcionais, Architecture Decision Records (ADRs), modelagem de domínio, diretrizes de LGPD e [backlog de issues](./docs/backlog-issues.md). | Markdown, Mermaid |

---

## Como Rodar o Projeto Localmente

### Pré-requisitos

- **Node.js** 20.x ou superior (recomendado Node 22 LTS)
- **pnpm** (ou **npm**)
- **Python** 3.12+ e **uv** *(para o módulo `apps/server`)*
- **Docker** e **Docker Compose** *(opcional para execução em contêiner e serviços de apoio)*

### 1. Executando o Frontend (`apps/web`)

1. Acesse o diretório da aplicação web e instale as dependências:
   ```bash
   cd apps/web
   pnpm install
   # ou: npm install
   ```

2. Inicie o servidor de desenvolvimento:
   ```bash
   pnpm run dev
   # ou: npm run dev
   ```

3. Abra no navegador em:
   ```text
   http://localhost:8443
   ```
   *(Para alterar a porta padrão `8443`, defina a variável `PORT`, ex.: `PORT=3000 pnpm run dev`).*

#### Credenciais de Demonstração do Protótipo (`apps/web`)

Você pode clicar em **"Acessar demonstração"** na tela inicial ou autenticar-se na instituição de exemplo (**Escola Municipal Horizonte**):

| Perfil | E-mail | Senha | Permissões Principais |
| :--- | :--- | :--- | :--- |
| **Administrador da instituição** | `marina@demo.com` | `demo123` | Acesso total, aprovação/devolução de documentos, edição da instituição e gestão de funcionários |
| **Funcionário** | `rafael@horizonte.edu.br` | `demo123` | Criação de documentos, envio para validação e consulta ao painel, modelos e auditoria |

#### Executando `apps/web` via Docker

```bash
docker build -t docflow-web ./apps/web
docker run --rm -p 8080:80 docflow-web
```
Acesse em `http://localhost:8080`.

---

## Documentação e Contribuição

- Consulte o [Backlog de Issues (`docs/backlog-issues.md`)](./docs/backlog-issues.md) para acompanhar o planejamento por milestones (`M0` a `M4`).
- Leia o nosso [Guia de Contribuição (`CONTRIBUTING.md`)](./CONTRIBUTING.md) para conhecer as convenções de branches, commits (Conventional Commits) e abertura de Pull Requests.
