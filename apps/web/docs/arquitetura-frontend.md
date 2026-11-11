# Arquitetura do Frontend (`apps/web/docs/arquitetura-frontend.md`)

Este documento descreve a organização interna, padrões de estado, roteamento e diretrizes de integração do frontend do **DocFlow** (`apps/web`).

---

## 1. Stack Principal

- **React 19 + TypeScript 5.7**
- **Vite 8** (bundler e dev server na porta padrão `8443`)
- **Tailwind CSS v4** (`@tailwindcss/vite`)
- **React Router** (roteamento protegido por perfil `ADMIN` / `EMPLOYEE`)
- **TanStack Query** (cache e sincronização com a API REST em `apps/server`)
- **Cliente HTTP tipado** gerado a partir de [`contracts/openapi.json`](../../../contracts/README.md)

---

## 2. Organização Modular por Funcionalidade (`src/`)

Na evolução do protótipo (`FE-01`), o código em `apps/web/src/` organiza-se por módulos de domínio de interface:

```text
apps/web/src/
├── app/                # Shell da aplicação, provedores globais e configuração de rotas
├── modules/
│   ├── auth/           # Login, cadastro de instituição + 1º admin e recuperação de senha
│   ├── media/          # Upload multipart de até 10 GB (partes de 50 MB), biblioteca e compressão
│   ├── transcripts/    # Player de vídeo/áudio sincronizado com editor de trechos e falantes
│   ├── templates/      # Catálogo e editor de modelos de documentos institucionais
│   ├── documents/      # Assistente de geração por IA, preenchimento de pendentes, revisão e aprovação
│   └── admin/          # Dashboard, gestão de usuários, configurações/cotas e trilha de auditoria
├── components/         # Design System compartilhado (botões, modais, tabelas, toasts, formulários)
└── lib/                # Cliente HTTP tipado (OpenAPI), tratamento de erros RFC 9457 e utilitários
```

---

## 3. Regras de Segurança e Integração no Frontend

1. **Zero Segredos no Cliente:** Variáveis `VITE_*` contêm apenas configurações públicas (como `VITE_API_BASE_URL`). Chaves de IA ou credenciais de storage jamais existem no frontend.
2. **Sem Senhas no `localStorage`:** Ao integrar com `apps/server`, nenhuma senha ou dado sensível é salvo em armazenamento local do navegador.
3. **Upload Multipart Direto para o Silo (`s3.<dominio>`):** O módulo `media` fatia o arquivo em blocos de **50 MB** e faz `PUT` diretamente nas URLs pré-assinadas do Silo com até **3 envios paralelos** e suporte a retomada.
4. **Acessibilidade e Usabilidade (`RNF-10`, `RNF-11`):** Interface 100% em `pt-BR`, responsiva e aderente à WCAG 2.1 AA (navegação por teclado, contraste e atributos ARIA).
