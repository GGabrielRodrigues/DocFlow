# Guia de Contribuição — DocFlow

Obrigado por contribuir com o **DocFlow**! Este documento define as convenções de organização, branches, mensagens de commit, testes e Pull Requests adotadas pelo time no monorepo.

---

## 1. Fluxo de Trabalho (Git Flow Simplificado)

Utilizamos a branch `main` como tronco principal sempre estável e pronta para deploy em ambiente de `staging`.

1. Identifique a issue correspondente no backlog ([`docs/backlog-issues.md`](./docs/backlog-issues.md)) ou nas Issues do GitHub.
2. Crie uma branch a partir da `main` atualizada.
3. Desenvolva a solução seguindo as práticas de qualidade e testes (TDD no domínio).
4. Faça commits pequenos, atômicos e padronizados com **Conventional Commits**.
5. Abra um **Pull Request (PR)** para `main` preenchendo o template do repositório.

---

## 2. Convenção de Nomenclatura de Branches

O nome da branch deve refletir o tipo de alteração, o identificador da issue (em letras minúsculas) e uma descrição curta em `kebab-case`:

```text
<tipo>/<id-da-issue>-<descricao-curta>
```

### Tipos de Branch Permitidos

| Prefixo | Uso | Exemplo |
| :--- | :--- | :--- |
| `feat/` | Nova funcionalidade de produto ou infraestrutura | `feat/be-04-cadastro-instituicao` |
| `fix/` | Correção de bug ou regressão | `fix/fe-06-retomada-upload-multipart` |
| `docs/` | Criação ou atualização de documentação e ADRs | `docs/doc-03-adr-monorepo` |
| `chore/` | Configuração, refatoração estrutural, CI/CD ou dependências | `chore/doc-01-estrutura-monorepo` |
| `test/` | Adição ou melhoria exclusiva de testes automatizados | `test/be-03-isolamento-multi-tenant` |
| `sec/` | Correções ou melhorias de segurança e hardening | `sec/be-05-rate-limit-login` |
| `spike/` | Investigação técnica ou prova de conceito | `spike/doc-06-comparativo-provedores-ia` |

---

## 3. Convenção de Commits (Conventional Commits)

Adotamos a especificação [Conventional Commits 1.0.0](https://www.conventionalcommits.org/pt-br/v1.0.0/). Toda mensagem de commit deve seguir o formato:

```text
<tipo>(<escopo>): <descrição curta no imperativo ou infinitivo>

[corpo opcional explicando o "porquê" da mudança]

[rodapé opcional: Refs: DOC-01, Closes #12, BREAKING CHANGE: ...]
```

### Tipos (`<tipo>`)

- `feat`: nova funcionalidade
- `fix`: correção de bug
- `docs`: alterações apenas em documentação (`docs/`, `README.md`, ADRs)
- `chore`: tarefas de manutenção, configuração de ferramentas, build ou dependências
- `refactor`: alteração de código que não corrige bug nem adiciona funcionalidade
- `test`: criação ou ajuste de testes automatizados
- `perf`: melhoria de desempenho
- `ci`: alterações em pipelines e workflows (`.github/workflows/`)
- `build`: alterações em Dockerfiles, empacotamento ou scripts de build
- `revert`: reversão de um commit anterior

### Escopos (`<escopo>`)

Recomendamos utilizar o módulo ou área afetada:
- `repo` / `monorepo`: estrutura raiz do repositório
- `docs`: documentação, requisitos e ADRs (`docs/`)
- `infra`: Terraform, Docker Compose, bootstrap e segredos (`infra/`)
- `server` ou submódulo (`identity`, `media`, `transcription`, `templates`, `documents`, `audit`): backend em `apps/server`
- `workers`: processamento assíncrono e integrações de IA em `apps/server`
- `web`: aplicação frontend em `apps/web`
- `contracts`: contratos OpenAPI em `contracts/`

### Regras para uma Boa Mensagem

- Escreva a descrição em **português**, iniciando com letra minúscula e **sem ponto final**.
- Limite a primeira linha a no máximo **72 caracteres**.
- Referencie o código da issue no escopo, na mensagem ou no rodapé (ex.: `Refs: DOC-01`).

### Exemplos

```text
chore(monorepo): reorganiza repositório na estrutura de monorepo (DOC-01)
```

```text
docs(adr): registra ADR-001 sobre organização do monorepo e módulos (DOC-03)
```

```text
feat(identity): implementa cadastro de instituição e primeiro administrador (BE-04)

Adiciona entidade Institution, validação de CNPJ no domínio e endpoint
POST /api/v1/institutions com testes unitários e de integração.

Refs: BE-04, RF-01, RN-02
```

---

## 4. Diretrizes de Pull Request (PR)

- **Escopo enxuto:** Cada PR deve resolver **uma única issue** do backlog sempre que possível.
- **Título do PR:** Siga o padrão `[ID-DA-ISSUE] Breve descrição` ou o formato Conventional Commits (ex.: `chore(monorepo): reorganizar repositório como monorepo [DOC-01]`).
- **Descrição completa:** Preencha todas as seções do template de PR (contexto, issue relacionada, mudanças realizadas e como testar).
- **Segurança em primeiro lugar:**
  - **Jamais** inclua segredos, chaves de API, senhas reais, arquivos `.env` ou `.tfstate` no PR.
  - Verifique se variáveis novas foram documentadas em `docs/variaveis-ambiente.md` e nos arquivos `.env.example`.
- **Verificações antes do merge:**
  - Todos os checks do CI (lint, typecheck, testes e validação de contratos/Terraform) devem estar verdes.
  - Ao menos **1 aprovação** de outro integrante da equipe é necessária antes do merge na `main`.

---

## 5. Padrões de Código e Qualidade

- **EditorConfig:** Certifique-se de que seu editor respeita o arquivo [`.editorconfig`](./.editorconfig) na raiz do projeto.
- **Frontend (`apps/web`):**
  - Execute `pnpm run format` e `pnpm run build` antes de abrir o PR.
- **Backend & Workers (`apps/server`):**
  - Desenvolvimento orientado a testes (**TDD**) para regras de negócio na camada `domain`.
  - Nenhum módulo de `domain` pode importar de `infrastructure` ou `api`.
  - Todo acesso a dados de negócio deve respeitar o isolamento multi-tenant (`institution_id`).

### 5.1. Guia de TDD no domínio

Para cada regra de negócio, siga o ciclo Red-Green-Refactor:

1. **Red:** escreva primeiro um teste unitário que descreva uma regra observável e falhe.
2. **Green:** implemente apenas o necessário para o teste passar.
3. **Refactor:** melhore nomes, estrutura e duplicação mantendo todos os testes verdes.

Os testes do domínio devem ser independentes de FastAPI, banco de dados, rede e
infraestrutura. Use `pytest` para casos determinísticos, `pytest-asyncio` para
casos assíncronos e `hypothesis` para invariantes que precisam ser verificadas
em várias entradas. A cobertura mínima configurada para `docflow.domain` é
80% do código Python implementado; quando os módulos de domínio forem
introduzidos, eles devem manter essa mesma exigência. Cobertura não substitui
testes de regras e casos-limite.

Comandos locais do backend:

```powershell
cd apps/server
poetry install
poetry run pytest --cov=docflow --cov-report=term-missing
poetry run ruff check src tests
poetry run mypy src
poetry run lint-imports
```
