# DocFlow Monorepo

Monorepo do **DocFlow** (React + Vite + Tailwind CSS em `apps/web`, backend FastAPI + Celery em `apps/server`, contratos em `contracts/`, infraestrutura em `infra/` e documentação em `docs/`).

## Project Structure

This is the canonical project structure. Start with task-relevant files below. Only follow imports or inspect other files when required, when a documented path is missing, or when the repository contradicts this guide.

- `apps/web/src/main.tsx` - React entrypoint; imports `src/index.css` and mounts `src/App.tsx` into the `#root` element
- `apps/web/src/App.tsx` - Primary application component and the usual starting point for UI work
- `apps/web/src/index.css` - Global CSS entrypoint and Tailwind CSS v4 import
- `apps/web/index.html` - Vite HTML shell containing the `#root` element and loading `src/main.tsx`
- `apps/web/package.json` - Project dependencies and the Vite build, development, preview, and formatting scripts
- `apps/web/vite.config.ts` - Vite configuration with React, Tailwind CSS v4, and Figma Make plugins plus the `@` alias for `src`
- `apps/server/` - Python 3.12+ / FastAPI modular monolith and Celery workers
- `contracts/` - Shared API contracts (OpenAPI)
- `infra/` - Infrastructure as Code (Terraform, Docker Compose, bootstrap)
- `docs/` - Requirements, ADRs, domain model, and backlog (`docs/backlog-issues.md`)

## Dependencies

- Runtime: React 19 and React DOM 19
- Styling: Tailwind CSS v4 with the `@tailwindcss/vite` plugin
- Build tooling: Vite 8, TypeScript 5.7, and `@vitejs/plugin-react`
- Formatting: oxfmt

## Styling

This project uses **Tailwind CSS v4** through the `@tailwindcss/vite` plugin configured in `vite.config.ts`. `src/index.css` imports Tailwind with `@import 'tailwindcss';`. Use Tailwind utility classes directly in JSX and put global CSS or Tailwind v4 theme customization in `src/index.css`. This scaffold does not need a Tailwind config file or PostCSS config.

`src/main.tsx` imports `src/index.css`, so global font wiring belongs in `src/index.css`. Keep CSS `@import` statements first, then add any `@font-face` rules and font-family defaults there.
