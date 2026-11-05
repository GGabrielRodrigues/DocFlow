# DocFlow — Automatizador de Atas e Documentos Administrativos

O **DocFlow** é um protótipo de sistema de gestão de documentos administrativos voltado para escolas e instituições públicas/privadas. O objetivo da aplicação é simplificar e padronizar a criação, validação e rastreabilidade de documentos institucionais — como **Atas**, **Ofícios** e **Prestações de contas** — centralizando o fluxo de trabalho da equipe em um único ambiente.

> **Nota:** Este projeto é um protótipo funcional demonstrativo. Toda a autenticação e persistência de dados acontecem localmente no navegador via `localStorage`, sem necessidade de configurar um banco de dados ou servidor backend externo.

---

## Ideia Geral e Funcionalidades

O sistema foi desenhado com suporte a múltiplas instituições (multi-tenant simulado) e controle de acesso baseado em dois perfis: **Administrador da instituição** e **Funcionário**.

### Principais Módulos
1. **Autenticação e Onboarding Institucional:**
   - Fluxo de boas-vindas com entrada em conta existente, acesso rápido ao modo de demonstração ou cadastro em duas etapas para novas instituições e seu primeiro administrador.
2. **Painel de Visão Geral (Dashboard):**
   - Indicadores rápidos do total de documentos, itens aguardando validação, documentos aprovados e membros da equipe.
   - Listagem das últimas movimentações de documentos e linha do tempo de atividades recentes.
3. **Gestão de Documentos:**
   - Consulta de todos os documentos da instituição com busca por título e filtro por status (`Rascunho`, `Em validação`, `Aprovado`, `Devolvido`).
   - Criação de novos documentos com seleção de tipo (`Ata`, `Ofício`, `Prestação de contas`) e vínculo a modelos pré-configurados, permitindo salvar como rascunho ou encaminhar diretamente para validação.
4. **Modelos de Documentos (Templates):**
   - Catálogo de estruturas padronizadas por tipo de documento para agilizar a redação administrativa.
5. **Fila de Validações:**
   - Área dedicada ao acompanhamento de documentos com status `Em validação`.
   - Administradores podem aprovar documentos ou devolvê-los aos responsáveis para ajustes.
6. **Auditoria e Rastreabilidade:**
   - Histórico cronológico detalhado de todas as ações executadas na instituição (acessos, criações, encaminhamentos, aprovações, devoluções e alterações cadastrais).
7. **Gestão da Instituição e Funcionários:**
   - Visualização e edição (exclusiva para administradores) dos dados cadastrais da instituição (CNPJ, e-mail, telefone, endereço).
   - Cadastro, edição de perfil (`Administrador` ou `Funcionário`) e ativação/inativação de contas da equipe.

---

## Credenciais de Demonstração

Ao abrir a aplicação, você pode clicar no botão **"Acessar demonstração"** na tela inicial ou entrar manualmente na instituição de exemplo (**Escola Municipal Horizonte**) com as seguintes contas pré-cadastradas:

| Perfil | E-mail | Senha | Permissões Principais |
| :--- | :--- | :--- | :--- |
| **Administrador da instituição** | `marina@demo.com` | `demo123` | Acesso total, aprovação/devolução de documentos, edição da instituição e gestão de funcionários |
| **Funcionário** | `rafael@horizonte.edu.br` | `demo123` | Criação de documentos, envio para validação e consulta ao painel, modelos e auditoria |

---

## Tecnologias Utilizadas

- **React 19** + **TypeScript 5.7**
- **Vite 8** (bundler e servidor de desenvolvimento)
- **Tailwind CSS v4** (`@tailwindcss/vite`) + CSS customizado (`src/index.css`)
- **oxfmt** (formatação de código)

---

## Como Rodar o Projeto Localmente

### Pré-requisitos

Certifique-se de ter instalado em sua máquina:
- **Node.js** (versão **20.x** ou superior recomendada — ex.: Node 22 LTS)
- Gerenciador de pacotes **pnpm** (ou **npm**, que já acompanha o Node.js)

### Passo a Passo

1. **Clone o repositório (caso ainda não esteja na pasta do projeto):**
   ```bash
   git clone <url-do-repositorio>
   cd automatizador-atas
   ```

2. **Instale as dependências:**
   Com `pnpm`:
   ```bash
   pnpm install
   ```
   Ou com `npm`:
   ```bash
   npm install
   ```

3. **Inicie o servidor de desenvolvimento:**
   Com `pnpm`:
   ```bash
   pnpm run dev
   ```
   Ou com `npm`:
   ```bash
   npm run dev
   ```

4. **Acesse no navegador:**
   Por padrão, o servidor Vite está configurado para subir na porta **8443** (ou na porta definida pela variável de ambiente `PORT`). Abra o navegador em:
   ```text
   http://localhost:8443
   ```
   *(Caso a porta `8443` já esteja em uso na sua máquina, você pode escolher outra porta executando `PORT=3000 pnpm run dev` ou `PORT=3000 npm run dev` e acessar `http://localhost:3000`).*

---

## Scripts Disponíveis

No arquivo `package.json`, você encontrará os seguintes comandos:

- `pnpm run dev` (ou `npm run dev`): Inicia o servidor de desenvolvimento com Hot Module Replacement (HMR).
- `pnpm run build` (ou `npm run build`): Gera a versão otimizada para produção na pasta `dist/`.
- `pnpm run preview` (ou `npm run preview`): Sobe um servidor local para visualizar a build de produção gerada.
- `pnpm run format` (ou `npm run format`): Formata os arquivos do projeto utilizando o `oxfmt`.

---

## Dica: Como Resetar os Dados do Protótipo

Como as alterações feitas durante o uso ficam salvas no `localStorage` do navegador (chaves `docflow-prototype-v2` e `docflow-session-v2`), caso queira restaurar os dados originais de fábrica:
1. Abra o **DevTools** do navegador (`F12` ou `Ctrl+Shift+I` / `Cmd+Option+I`).
2. Vá até a aba **Application** (Aplicativo) > **Local Storage** (Armazenamento Local).
3. Remova as chaves `docflow-prototype-v2` e `docflow-session-v2` e recarregue a página.
