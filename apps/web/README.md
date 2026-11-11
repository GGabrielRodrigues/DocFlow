# DocFlow Web (`apps/web`)

Frontend web do **DocFlow** construído com **React 19**, **TypeScript 5.7**, **Vite 8** e **Tailwind CSS v4**.

Atualmente contém o protótipo funcional demonstrativo do sistema de gestão de documentos administrativos (Atas, Ofícios e Prestações de contas), que será progressivamente integrado à API em `apps/server`.

---

## Funcionalidades do Protótipo

- **Autenticação e Onboarding Institucional:** Entrada em conta existente, modo de demonstração ou cadastro em duas etapas para novas instituições e seu primeiro administrador.
- **Painel de Visão Geral (Dashboard):** Indicadores rápidos do total de documentos, itens em validação, aprovados e membros da equipe.
- **Gestão de Documentos:** Busca por título, filtro por status (`Rascunho`, `Em validação`, `Aprovado`, `Devolvido`) e criação vinculada a modelos.
- **Modelos de Documentos (Templates):** Catálogo de estruturas padronizadas por tipo de documento.
- **Fila de Validações:** Aprovação ou devolução de documentos por administradores.
- **Auditoria e Rastreabilidade:** Histórico cronológico detalhado das ações na instituição.
- **Gestão da Instituição e Funcionários:** Edição cadastral e gerenciamento de contas e perfis (`Administrador da instituição` e `Funcionário`).

### Credenciais de Demonstração

| Perfil | E-mail | Senha | Permissões Principais |
| :--- | :--- | :--- | :--- |
| **Administrador da instituição** | `marina@demo.com` | `demo123` | Acesso total, aprovação/devolução de documentos, edição da instituição e gestão de funcionários |
| **Funcionário** | `rafael@horizonte.edu.br` | `demo123` | Criação de documentos, envio para validação e consulta ao painel, modelos e auditoria |

---

## Como Rodar (`apps/web`)

```bash
cd apps/web
pnpm install   # ou npm install
pnpm run dev   # ou npm run dev
```

Por padrão, o servidor Vite sobe em `http://localhost:8443` (ou na porta definida por `PORT`).

### Scripts Disponíveis

- `pnpm run dev` (ou `npm run dev`): Inicia o servidor de desenvolvimento com HMR.
- `pnpm run build` (ou `npm run build`): Gera a build de produção em `dist/`.
- `pnpm run preview` (ou `npm run preview`): Visualiza localmente a build de produção.
- `pnpm run format` (ou `npm run format`): Formata os arquivos com `oxfmt`.
