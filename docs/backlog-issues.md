# DocFlow — Backlog de Issues

## Convenções

**Labels de área:** `docs`, `infra`, `backend`, `workers`, `frontend`
**Labels de tipo:** `feature`, `chore`, `spike`, `security`, `test`
**Tamanho:** `S` (≤½ dia), `M` (1–2 dias), `L` (3–5 dias)
**Milestones**
- **M0 – Fundação:** repositório, decisões, infra base, CI
- **M1 – Núcleo:** auth, multi-tenant, upload
- **M2 – Transcrição:** transcrição com diarização e editor
- **M3 – Documentos:** modelos, geração por IA, validação, exportação
- **M4 – Complementos e produção:** compressão, retenção/LGPD, observabilidade, hardening

**Premissas adotadas:** SaaS multi-instituição; backend e workers em Python (FastAPI + Celery); front React/TS; transcrição e LLM em nuvem atrás de interfaces; Terraform com estado no HCP Terraform; segredos no Infisical; deploy em **servidor próprio (on-premise)** com Docker Compose; storage S3 compatível self-hosted (Silo, fork do MinIO).

> [!NOTE]
> Sugestão de divisão para 3 pessoas: **A** = backend + workers, **B** = frontend + documentação, **C** = infra + CI + apoio no backend. Cada issue tem `Depende de` para ajudar a ordenar.

---

# 📄 DOCUMENTAÇÃO

### DOC-01 · Reorganizar o repositório como monorepo `[M0][docs][chore][S]`
Mover o protótipo atual para `apps/web`, criar `apps/server`, `infra`, `docs`, `contracts`.
- [x] Estrutura de pastas criada e protótipo funcionando em `apps/web`
- [x] `README.md` raiz explicando módulos e como rodar
- [x] `CONTRIBUTING.md` com convenção de branches, commits (Conventional Commits) e PRs
- [x] `.gitignore` e `.editorconfig` raiz
- [x] Templates de issue e de pull request em `.github/`

### DOC-02 · Versionar o documento de requisitos em `docs/` `[M0][docs][chore][S]`
- [x] RFs, RNFs e RNs em `docs/docflow_requisitos.md` com IDs estáveis (RF-xx, RNF-xx, RN-xx)
- [x] Pontos em aberto transformados em ADRs ou issues (e decisões consolidadas nos requisitos)
- [x] Matriz de rastreabilidade inicial (requisito → issue)

### ~~DOC-03 · ADR-001: Monorepo e organização de módulos `[M0][docs][S]`~~ *(Descartada — já coberta pelo README raiz e estrutura da DOC-01)*

### DOC-04 · Documentação da Stack (`docs/stack.md`: Python/FastAPI, React/TS, PostgreSQL, Redis, S3) `[M0][docs][S]`
- [x] Documento `docs/stack.md` de fácil entendimento detalhando a stack, responsabilidades e integração entre componentes

### DOC-05 · Arquitetura de monolito modular com API e workers no mesmo código-base (`apps/server/README.md`) `[M0][docs][S]`
- [x] Explicação clara documentada diretamente em `apps/server/README.md`

### DOC-06 · Provedores de IA atrás de interfaces (`docs/provedores-ia.md`: `TranscriptionProvider`, `LLMProvider`) `[M0][docs][spike][M]`
- [x] Comparativo de pelo menos 3 provedores de transcrição com diarização em PT-BR (qualidade, preço/hora, limites de arquivo, DPA/LGPD, região dos dados)
- [x] Comparativo de LLMs (custo, saída estruturada, retenção de dados)
- [x] Decisão do provedor inicial (Deepgram Nova-3 + Gemini 2.5 Flash) e plano de troca documentados em `docs/provedores-ia.md`

### DOC-07 · Documentação da Infraestrutura (`infra/`: Terraform + HCP Terraform Cloud + Infisical + Docker Socket + Cloudflare Tunnel) `[M0][docs][S]`
- [x] Registrar que a hospedagem é **servidor próprio on-premise** e a exposição externa (DNS + TLS) é provida pelo **Cloudflare Tunnel (`cloudflared`)** (`infra/README.md` e `infra/catalogo-modulos.md`)
- [x] Explicar a estrutura em 3 camadas nos 4 domínios (`databases`, `apps`, `tools`, `observability`), o mapeamento dos 2 `Dockerfile`s (`web` e `server`), o uso do **HCP Terraform Cloud (tier gratuito)** e a conexão híbrida via socket do Docker (`unix:///var/run/docker.sock`) ou SSH (`docker_ssh_host`)
- [x] Descrever o fluxo de estado remoto e o inventário completo de variáveis/segredos no Infisical (`infra/variaveis-e-segredos.md` e `infra/AGENTS.md`)
- [x] Listar providers Terraform usados: `kreuzwerker/docker` (`~> 3.0.1`) e `infisical/infisical` (`~> 0.16.0`)

### DOC-08 · Estratégia de Multi-tenancy (`docs/multi-tenancy.md`: coluna `institution_id` + RLS) `[M0][docs][S]`
- [x] Decisão documentada em `docs/multi-tenancy.md`: tabela compartilhada com coluna `institution_id` obrigatória + Row-Level Security (RLS) do PostgreSQL como defesa em profundidade e isolamento por prefixo no Silo (S3)

### DOC-09 · Estratégia de upload de 10 GB (`docs/upload-multipart.md`: multipart direto no Silo/S3) `[M0][docs][S]`
- [x] Estratégia documentada em `docs/upload-multipart.md`: partes de 50 MB (compatível com o limite de 100 MB do Cloudflare Tunnel), 3 envios paralelos, validação dupla de 10 GB / 2h30, CORS com exposição de `ETag` e limpeza de uploads abandonados em 24h

### DOC-10 · Modelo de domínio e diagrama ER (`docs/modelo-dominio.md`) `[M0][docs][M]`
Entidades: Institution, User, Media, Transcript, Speaker, TranscriptSegment, Template, TemplateVersion, Document, DocumentVersion, AuditLog, Job, Usage.
- [x] Diagrama ER (Mermaid) e glossário (linguagem ubíqua) em `docs/modelo-dominio.md`
- [x] Máquina de estados de Document, Media e Job em `docs/modelo-dominio.md`

### DOC-11 · Contrato inicial da API (`contracts/README.md` — OpenAPI) `[M0][docs][M]`
Depende de DOC-10.
- [x] Esboço completo de endpoints por contexto (`/api/v1/...`), convenções de erro (RFC 9457), paginação e autenticação documentados em `contracts/README.md`

### DOC-12 · Política de privacidade e LGPD do produto `[M4][docs][M]`
- [ ] Mapeamento de dados pessoais tratados (vídeo, voz, nomes, transcrições)
- [ ] Bases legais, papéis (controlador/operador), retenção, subprocessadores (provedores de IA)
- [ ] Rascunho de Termos de Uso e Política de Privacidade

### DOC-13 · Validação de hipóteses com usuários `[M1][docs][spike][M]`
- [ ] Roteiro de entrevista; ao menos 3 entrevistas (secretaria, escola, ONG)
- [ ] Resumo com ajustes ao escopo e aos modelos de documento prioritários

### DOC-14 · Coletar modelos de documento reais (ata, ofício, prestação de contas) `[M3][docs][S]`
Anonimizados, para uso como modelos padrão e conjunto de avaliação da IA.

### DOC-15 · Guia de desenvolvimento local e runbook de operação `[M4][docs][M]`
- [ ] Setup local em um comando
- [ ] Runbook: deploy, rollback, rotação de segredos, restore de backup, incidentes comuns

---

# 🏗️ INFRAESTRUTURA

> [!IMPORTANT]
> Regras gerais: nenhum segredo no repositório nem em arquivo `.tfvars` versionado; estado **somente** no HCP Terraform; variáveis de ambiente das aplicações **somente** via Infisical.

### INF-01 · Criar organização e projeto no HCP Terraform `[M0][infra][chore][S]`
- [ ] Organização, projeto e workspaces `docflow-staging` e `docflow-prod`
- [ ] Execution mode **Agent** (o agent roda no servidor on-premise, ver INF-19); alternativa documentada: modo local com estado remoto
- [ ] Pool de agents criado e token do agent guardado no Infisical
- [ ] Membros do time convidados com permissões adequadas
- [ ] Token de API guardado de forma segura (não no repo)

### INF-02 · Estrutura Terraform base com backend `cloud` `[M0][infra][chore][M]`
Depende de INF-01.
- [ ] `infra/terraform/` com módulos (`network`, `compute`, `storage`, `dns`) e ambientes (`staging`, `prod`)
- [ ] Bloco `terraform { cloud { ... } }` apontando ao workspace correto
- [ ] Versão do Terraform e providers fixadas; `.terraform.lock.hcl` versionado
- [ ] `terraform init` funciona e o `.tfstate` **não** existe localmente
- [ ] `.gitignore` bloqueando `*.tfstate*`, `*.tfvars` com segredos, `.terraform/`

### INF-03 · Configurar Infisical (projeto, ambientes e pastas) `[M0][infra][security][S]`
- [ ] Projeto `docflow` com ambientes `dev`, `staging`, `prod`
- [ ] Pastas por serviço (`/api`, `/worker`, `/web`, `/infra`)
- [ ] Inventário de variáveis (`docs/variaveis-ambiente.md`) sem valores
- [ ] Controle de acesso por papel e por ambiente

### INF-04 · Machine Identities do Infisical e integração com o HCP Terraform `[M0][infra][security][M]`
Depende de INF-01, INF-03.
- [ ] Identity para o Terraform (credenciais armazenadas como variáveis sensíveis do workspace no HCP)
- [ ] Identity de leitura por servidor/ambiente para os contêineres
- [ ] Credenciais com escopo mínimo e plano de rotação
- [ ] Verificar que segredos lidos pelo Terraform não vazam em outputs/estado (usar `sensitive`, evitar gravar valores no estado; preferir ephemeral resources quando disponível)

### INF-05 · Preparar e inventariar o servidor on-premise (compute) `[M0][infra][feature][M]`
Depende de INF-02, DOC-07.
- [ ] Levantar especificações do servidor (CPU, RAM, disco, rede, SO) e documentar em `docs/infra/servidor.md`
- [ ] Instalar/atualizar o SO (LTS), usuário de deploy sem root, acesso SSH apenas por chave
- [ ] Separação staging/prod no mesmo servidor (redes e projetos Compose distintos) ou VMs; decisão documentada
- [ ] Firewall (ufw/nftables): apenas 22 (restrito à rede interna/VPN), 80 e 443 abertos
- [ ] IP fixo interno e nome na rede
- [ ] Terraform gerenciando o que for possível via SSH (provider Docker, arquivos de configuração); o que não for fica documentado como passo manual de bootstrap

### INF-06 · Subir object storage self-hosted (Silo — fork do MinIO) e provisionar buckets `[M0][infra][feature][M]`
Depende de INF-02, INF-05.
- [ ] Silo no servidor (container ou serviço) com disco dedicado e credenciais root no Infisical
- [ ] Buckets, políticas e usuários criados via Terraform (provider compatível S3/`aminueza/minio`)
- [ ] Buckets separados: `media-raw`, `media-processed`, `documents`
- [ ] Acesso privado, criptografia em repouso, versionamento nos documentos
- [ ] **CORS** configurado para upload multipart do navegador (expor header `ETag`)
- [ ] Regras de ciclo de vida (limpeza de multipart incompleto, expiração por retenção)
- [ ] Endpoint do Silo acessível pelo **navegador do usuário** via HTTPS (ex.: `s3.<domínio>`), necessário para o upload multipart direto
- [ ] Capacidade de disco dimensionada para vídeos de até 10 GB por upload e alerta de uso
- [ ] Credenciais de aplicação com permissão mínima, gravadas no Infisical

### INF-07 · DNS e certificados TLS `[M1][infra][feature][M]`
Depende de INF-20.
- [ ] Domínio e provedor de DNS definidos; registros `app.`, `api.`, `s3.` (staging e prod) via Terraform
- [ ] Certificado TLS automático (Let's Encrypt), preferencialmente por desafio **DNS-01** (token do DNS no Infisical)
- [ ] Atualização automática de DNS caso o IP público seja dinâmico

### INF-08 · Preparar o servidor (bootstrap) `[M1][infra][feature][M]`
Depende de INF-05.
- [ ] Instalar Docker e Compose plugin (script idempotente versionado em `infra/bootstrap/`)
- [ ] Instalar Infisical CLI/Agent no servidor e autenticar com a Machine Identity
- [ ] Hardening: fail2ban, SSH somente por chave, `unattended-upgrades`
- [ ] Rotação de logs do Docker configurada

### INF-09 · Docker Compose de produção/staging `[M1][infra][feature][L]`
Depende de INF-08.
- [ ] Serviços: `proxy` (Caddy ou Traefik), `web`, `api`, `worker-io`, `worker-cpu`, `postgres`, `redis`
- [ ] Segredos injetados via `infisical run -- docker compose up` ou Infisical Agent; **nenhum `.env` com valor real no repo**
- [ ] Healthchecks, `restart: unless-stopped`, limites de recursos
- [ ] Volumes persistentes para Postgres e Redis
- [ ] Rede interna isolada: apenas o proxy exposto

### INF-10 · Subir o PostgreSQL e rodar migrações no servidor `[M1][infra][feature][M]`
Depende de INF-09, BE-03.
- [ ] Postgres iniciado e acessível apenas pela rede interna
- [ ] Job de migração (Alembic) executado a cada deploy antes de subir a API
- [ ] Backup diário automatizado (pg_dump criptografado) com retenção, copiado para **local externo ao servidor** (disco externo, outra máquina ou storage em nuvem barato)
- [ ] **Teste de restauração documentado**

### INF-11 · Subir Redis e os workers no servidor `[M2][infra][feature][M]`
Depende de INF-09, WK-01.
- [ ] Redis com persistência (AOF) e senha
- [ ] Workers com concorrência configurável via variável (Infisical)
- [ ] Worker de CPU com limite de memória/CPU separado para FFmpeg
- [ ] Reinício automático e *graceful shutdown* sem perder jobs

### INF-12 · Subir API e frontend no servidor `[M1][infra][feature][M]`
Depende de INF-09, BE-01, FE-01.
- [ ] Imagens publicadas no GHCR (ou registry escolhido)
- [ ] API atrás do proxy em `api.<domínio>`, front em `app.<domínio>`
- [ ] `/health` e `/ready` verificados no deploy
- [ ] Limite de corpo de requisição adequado (uploads vão direto ao S3)

### INF-13 · Pipeline CI/CD de infraestrutura `[M1][infra][chore][M]`
Depende de INF-02.
- [ ] `terraform fmt`, `validate`, `tflint` e `trivy config`/`checkov` em PRs
- [ ] `plan` no PR (speculative plan do HCP) e `apply` apenas após merge, com aprovação para prod
- [ ] Nenhum segredo em logs do CI

### INF-14 · Pipeline CI/CD de deploy da aplicação `[M1][infra][chore][L]`
Depende de INF-12.
- [ ] Build e push de imagens por commit (tags imutáveis por SHA)
- [ ] Deploy automático em staging após merge na `main`; prod por aprovação manual
- [ ] Deploy por SSH/Compose pull com `infisical run`; rollback para a tag anterior em um comando
- [ ] Notificação de sucesso/falha

### INF-15 · Observabilidade `[M4][infra][feature][L]`
- [ ] Logs estruturados centralizados (Loki/Grafana ou serviço gerenciado)
- [ ] Métricas (Prometheus/Grafana): API, fila, tempo de jobs, uso de CPU/disco
- [ ] Erros no Sentry (DSN no Infisical)
- [ ] Alertas: serviço fora, fila crescendo, disco > 80%, backup falhou
- [ ] Monitoramento externo de uptime

### INF-16 · Ambiente de desenvolvimento local `[M0][infra][chore][M]`
- [ ] `docker-compose.dev.yml` com Postgres, Redis, Silo (S3) e Mailpit
- [ ] Segredos de dev via Infisical (`infisical run`), com `.env.example` apenas com nomes
- [ ] `make up`/`make test` (ou `just`) documentados

### INF-17 · Segurança e hardening em produção `[M4][infra][security][M]`
- [ ] Revisão de portas, usuários e permissões
- [ ] Varredura de imagens (Trivy) no CI
- [ ] Rotação de segredos testada ao menos uma vez
- [ ] Política de retenção de logs e acesso mínimo ao servidor

### INF-18 · Estimativa e controle de custos `[M4][infra][chore][S]`
- [ ] Planilha de custo mensal (energia, internet, backup externo, transcrição/h, LLM)
- [ ] Alertas de orçamento nos provedores de IA

### INF-19 · Instalar HCP Terraform Agent no servidor `[M0][infra][feature][M]`
Depende de INF-01, INF-05.
- [ ] Agent rodando como serviço (container ou systemd) com token do pool, reinício automático e saída apenas (outbound HTTPS, sem porta de entrada)
- [ ] Workspaces `docflow-staging` e `docflow-prod` configurados para executar no pool de agents
- [ ] Teste de `plan` e `apply` de ponta a ponta com um recurso trivial
- [ ] Token do agent e procedimento de rotação documentados

### INF-20 · Exposição segura do servidor à internet `[M1][infra][security][M]`
Depende de INF-05.
- [ ] Verificar viabilidade: IP público, CG-NAT, bloqueio de portas pelo provedor de internet
- [ ] Escolher a forma de exposição: redirecionamento de portas 80/443 **ou** túnel (Cloudflare Tunnel/Tailscale Funnel) — decisão em ADR
- [ ] Rede separada (DMZ/VLAN) ou isolamento por firewall do restante da rede local
- [ ] Acesso administrativo (SSH, painéis) somente por VPN (ex.: WireGuard/Tailscale)
- [ ] Proteção básica contra abuso (rate limit no proxy, fail2ban, CrowdSec opcional)

### INF-21 · Resiliência do servidor on-premise `[M4][infra][chore][M]`
- [ ] Nobreak/UPS e desligamento seguro, ou risco aceito e documentado
- [ ] Monitoramento de disco (SMART), temperatura e RAID/espelhamento, conforme hardware
- [ ] Plano de recuperação de desastre: reconstruir o servidor do zero a partir do Terraform, do bootstrap e dos backups, com tempo medido
- [ ] Reinício automático dos serviços após queda de energia

---

# ⚙️ BACKEND (Python / FastAPI)

### BE-01 · Scaffold do backend `[M0][backend][chore][M]`
- [ ] `apps/server` com `uv`, Python 3.12+, FastAPI, estrutura modular (`identity`, `media`, `transcription`, `templates`, `documents`, `audit`, `shared`)
- [ ] Camadas por módulo: `domain`, `application`, `infrastructure`, `api`
- [ ] Configuração via `pydantic-settings` (variáveis vindas do ambiente/Infisical)
- [ ] `/health` e `/ready`
- [ ] Logging estruturado com `request_id`

### BE-02 · Qualidade e testes (TDD) `[M0][backend][test][M]`
- [ ] `pytest`, `pytest-asyncio`, `hypothesis`, cobertura mínima (ex.: 80% no domínio)
- [ ] `ruff` + `mypy --strict` (ou `pyright`)
- [ ] `import-linter` para impedir que `domain` dependa de `infrastructure`
- [ ] Pre-commit e CI executando tudo (ver INF-13/CI)
- [ ] Guia de TDD no `CONTRIBUTING.md`

### BE-03 · Banco de dados, migrações e multi-tenancy `[M0][backend][feature][M]`
Depende de DOC-08, DOC-10.
- [ ] SQLAlchemy 2 + Alembic; migração inicial
- [ ] Todo registro de negócio com `institution_id`
- [ ] Repositório base que **sempre** filtra por tenant; RLS do Postgres como segunda barreira
- [ ] Testes provando que o tenant A não lê dados do tenant B (RN-01)

### BE-04 · Identidade: cadastro de instituição e primeiro administrador `[M1][backend][feature][M]`
Cobre RF-01, RN-02.
- [ ] Endpoint de cadastro (instituição + administrador) com validação de CNPJ
- [ ] Testes de domínio primeiro (TDD)

### BE-05 · Autenticação e sessão `[M1][backend][security][L]`
Cobre RF-02, RNF-05, RN-04.
- [ ] Login com e-mail/senha (Argon2), JWT de acesso curto + refresh com rotação
- [ ] Logout, recuperação e troca de senha por e-mail com token de uso único
- [ ] Rate limiting e bloqueio temporário contra força bruta
- [ ] Usuário inativo não autentica
- [ ] MFA (TOTP) como item opcional separado

### BE-06 · Gestão de usuários e autorização (RBAC) `[M1][backend][feature][M]`
Cobre RF-03, RF-04, RN-02, RN-03, RN-04.
- [ ] CRUD de usuários pelo administrador; perfis (`Administrador`, `Funcionário`)
- [ ] Impedir inativar/remover o último administrador
- [ ] Dependência de autorização reutilizável (`require_role`, `require_permission`)

### BE-07 · Trilha de auditoria `[M1][backend][feature][M]`
Cobre RF-27, RN-11, RNF-09.
- [ ] Serviço `AuditLog` append-only (sem update/delete, inclusive por permissão do banco)
- [ ] Eventos: login, upload, geração, edição, aprovação, devolução, exportação, exclusão
- [ ] Endpoint paginado com filtros para administrador

### BE-08 · Mídia: upload multipart de até 10 GB `[M1][backend][feature][L]`
Cobre RF-05, RF-06, RN-05, RNF-03. Depende de INF-06, DOC-09.
- [ ] Endpoints: iniciar upload, assinar partes (presigned), completar, abortar
- [ ] Validação de tamanho (≤ 10 GB) e tipo **antes** de iniciar
- [ ] Limpeza de uploads abandonados
- [ ] Após completar: verificar objeto, extrair metadados (duração, codec) via worker e criar `Media`
- [ ] Testes com Silo/S3 (Testcontainers)

### BE-09 · Mídia: listagem, detalhe, download e exclusão `[M1][backend][feature][M]`
Cobre RF-07, RN-13, RN-14.
- [ ] URLs assinadas e temporárias para pré-visualização/download
- [ ] Exclusão remove arquivos do storage e dados derivados
- [ ] Controle de acesso: autor, administradores e compartilhados

### BE-10 · Jobs: modelo, fila e acompanhamento `[M1][backend][feature][M]`
Cobre RF-09, RNF-04. Depende de WK-01.
- [ ] Entidade `Job` (tipo, estado, progresso, erro, tentativas) e máquina de estados
- [ ] Endpoints de status, cancelamento e reprocessamento
- [ ] SSE (ou polling) para o front acompanhar progresso
- [ ] Idempotência: reenviar o mesmo job não duplica efeitos

### BE-11 · Transcrição: casos de uso e API `[M2][backend][feature][L]`
Cobre RF-10, RF-13, RF-14. Depende de BE-10, WK-03.
- [ ] Solicitar transcrição de uma mídia (idioma, nº esperado de falantes opcional)
- [ ] Modelos `Transcript`, `Speaker`, `TranscriptSegment` (início, fim, texto, confiança)
- [ ] Obter transcrição paginada/por trecho
- [ ] Exportar TXT, DOCX, SRT/VTT

### BE-12 · Transcrição: edição de texto e de falantes `[M2][backend][feature][M]`
Cobre RF-11, RF-12, RN-17.
- [ ] Editar texto de segmentos, reatribuir falante, renomear falante (propaga em todos os trechos), mesclar falantes
- [ ] Versionamento simples das edições e auditoria

### BE-13 · Modelos de documento: CRUD e versionamento `[M3][backend][feature][L]`
Cobre RF-15, RF-16, RN-12.
- [ ] Modelo com campos tipados (texto, data, lista, obrigatório, validação) e corpo (DOCX/template)
- [ ] Versão imutável por publicação; ativar/desativar
- [ ] Modelos padrão do sistema (ata, ofício, memorando, prestação de contas), com seed
- [ ] Testes de domínio para versionamento

### BE-14 · Geração de documento por IA (orquestração) `[M3][backend][feature][L]`
Cobre RF-18, RF-19, RF-20, RN-06, RN-08. Depende de BE-13, WK-05.
- [ ] Caso de uso: selecionar modelo + transcrições + informações extras, disparar geração assíncrona
- [ ] Resultado em campos estruturados: valor, evidência (trecho/timestamp), confiança, status `preenchido`/`pendente`/`ambíguo`
- [ ] Documento nasce como Rascunho
- [ ] Endpoint para o usuário completar campos pendentes

### BE-15 · Documento: edição, regeneração de seções e versões `[M3][backend][feature][L]`
Cobre RF-21, RF-26, RN-09.
- [ ] Edição do conteúdo; regenerar uma seção
- [ ] Histórico de versões, diff e restauração
- [ ] Aprovado é imutável; edição cria nova versão em Rascunho

### BE-16 · Fluxo de validação e aprovação `[M3][backend][feature][M]`
Cobre RF-24, RF-25, RN-06, RN-07, RN-08, RN-10.
- [ ] Máquina de estados: Rascunho → Em validação → Aprovado/Devolvido
- [ ] A pessoa que solicitou a geração do documento atua como validadora (seja Administrador ou Funcionário, conforme RN-07)
- [ ] Devolução exige justificativa
- [ ] Bloquear aprovação com campos obrigatórios pendentes
- [ ] Notificações (e-mail) ao validador/solicitante
- [ ] Suíte extensa de testes de domínio (TDD)

### BE-17 · Revisão automática do documento `[M3][backend][feature][M]`
Cobre RF-22. Depende de WK-06.
- [ ] Endpoint que solicita revisão (inconsistências, ortografia, divergências com o modelo) e devolve sugestões acionáveis

### BE-18 · Exportação de documento (DOCX/PDF) `[M3][backend][feature][M]`
Cobre RF-23.
- [ ] Renderizar DOCX a partir do modelo e converter para PDF (ex.: LibreOffice headless no worker)
- [ ] Armazenar e entregar por URL assinada; registrar na auditoria

### BE-19 · Busca, filtros e dashboard `[M3][backend][feature][M]`
Cobre RF-28, RF-29.
- [ ] Busca de documentos/mídias/transcrições (começar com `tsvector` do Postgres)
- [ ] Endpoint de métricas do dashboard

### BE-20 · Cotas e consumo `[M4][backend][feature][M]`
Cobre RN-16, RNF-16.
- [ ] Registro de uso por instituição (minutos transcritos, GB armazenados, tokens)
- [ ] Bloqueio de novos jobs ao exceder a cota e aviso ao administrador

### BE-21 · Retenção e direitos do titular (LGPD) `[M4][backend][security][L]`
Cobre RF-30, RF-31, RN-14, RN-15, RNF-07.
- [ ] Política de retenção configurável por instituição, executada por rotina agendada
- [ ] Exportação e exclusão de dados de um titular
- [ ] Habilitação explícita de provedor de IA externo por instituição (RN-15)

### BE-22 · Segurança da API `[M4][backend][security][M]`
- [ ] Cabeçalhos de segurança, CORS restrito, limite de tamanho de payload, validação rigorosa de entrada
- [ ] Revisão do OWASP API Top 10 (principalmente BOLA/IDOR entre tenants)
- [ ] `pip-audit` e análise estática (bandit) no CI

### BE-23 · Geração do contrato OpenAPI para o front `[M1][backend][chore][S]`
- [ ] Publicar `openapi.json` em `contracts/` a cada mudança; falhar o CI se estiver desatualizado

### BE-24 · Notificações por e-mail `[M1][backend][feature][M]`
- [ ] Porta `EmailSender` com adaptador SMTP/provedor; templates (convite, reset de senha, documento para validar, job concluído)

---

# 🔧 WORKERS (processamento assíncrono e IA)

### WK-01 · Infraestrutura de workers (Celery + Redis) `[M1][workers][chore][M]`
- [ ] Celery configurado no mesmo código-base do backend, com filas separadas: `io`, `cpu`, `ai`
- [ ] Retentativas com *backoff*, `acks_late`, *visibility timeout* adequado para tarefas longas
- [ ] Jobs idempotentes e atualização de progresso/estado na entidade `Job`
- [ ] Tratamento de falha e *dead letter* (fila de jobs falhados)

### WK-02 · Extração de metadados e validação de mídia `[M1][workers][feature][M]`
Cobre RF-06, RN-05.
- [ ] `ffprobe`: duração (validar limite máximo de 2h30), codecs, resolução, áudio presente
- [ ] Rejeitar arquivo corrompido, sem áudio ou acima de 2h30 com mensagem clara

### WK-03 · Interface `TranscriptionProvider` + primeiro adaptador `[M2][workers][feature][L]`
Cobre RF-10, RF-11. Depende de DOC-06.
- [ ] Interface (Protocol) e **fake** determinístico para testes
- [ ] Adaptador do provedor escolhido com diarização, tratamento de limites, erros e *rate limit*
- [ ] Mapeamento para o modelo interno (segmentos, falantes, confiança)
- [ ] Testes de contrato do adaptador

### WK-04 · Pipeline de transcrição `[M2][workers][feature][L]`
Cobre RF-09, RF-10, RNF-01. Depende de WK-02, WK-03.
- [ ] Extrair/normalizar o áudio com FFmpeg (mono, 16 kHz) **sem baixar 10 GB para memória** (streaming/disco temporário com limpeza)
- [ ] Enviar áudio (não o vídeo) ao provedor; acompanhar por webhook ou *polling*
- [ ] Persistir resultado; atualizar progresso; limpar arquivos temporários
- [ ] Cancelamento, retentativa e tratamento de arquivos longos (chunking se o provedor exigir)

### WK-05 · Interface `LLMProvider` + saída estruturada `[M3][workers][feature][L]`
Cobre RNF-12. Depende de DOC-06.
- [ ] Interface com **fake** e adaptador do provedor escolhido
- [ ] Saída estruturada validada por Pydantic (reparo/retentativa em caso de saída inválida)
- [ ] Controle de custo (contagem de tokens) e *timeouts*

### WK-06 · Agente de geração de documentos `[M3][workers][feature][L]`
Cobre RF-18, RF-19, RF-20, RN-08. Depende de WK-05.
- [ ] Prompts versionados por tipo de documento (ata, ofício, prestação de contas)
- [ ] Extração de participantes, pauta, decisões, responsáveis, prazos e encaminhamentos
- [ ] Cada campo com evidência (timestamps/trechos); **sem evidência → `pendente`**, nunca valor inventado
- [ ] Transcrições longas: segmentação (map-reduce) respeitando o contexto do modelo
- [ ] Proteção contra *prompt injection* vindo da transcrição (conteúdo tratado como dado)

### WK-07 · Agente de revisão `[M3][workers][feature][M]`
Cobre RF-22. Verifica inconsistências, ortografia e aderência ao modelo, devolvendo sugestões estruturadas.

### WK-08 · Suíte de avaliação da IA (evals) `[M3][workers][test][L]`
Cobre RNF-12. Depende de DOC-14.
- [ ] Conjunto de referência (transcrições + documentos esperados, anonimizados)
- [ ] Métricas: WER e DER para transcrição; precisão/recall dos campos, taxa de alucinação (valor sem evidência) para documentos
- [ ] Execução manual/agendada (não bloqueia o CI normal) com relatório comparável entre versões de prompt/modelo

### WK-09 · Worker de compressão de vídeo `[M4][workers][feature][L]`
Cobre RF-08, RN-18.
- [ ] Perfis predefinidos (leve, alta qualidade, somente áudio) com FFmpeg
- [ ] Progresso por parse de saída do FFmpeg; saída como novo arquivo (nunca sobrescreve o original)
- [ ] Mostrar tamanho antes/depois; limites de CPU/tempo; fila `cpu` isolada
- [ ] Testes com vídeos pequenos de fixture

### WK-10 · Worker de exportação (DOCX/PDF) `[M3][workers][feature][M]`
Cobre RF-23. Preenche o modelo DOCX, converte para PDF e salva no storage.

### WK-11 · Tarefas agendadas `[M4][workers][feature][M]`
- [ ] Celery Beat: retenção/expiração (BE-21), limpeza de uploads abandonados e de arquivos temporários, consolidação de uso (BE-20)

---

# 🎨 FRONTEND (React / TypeScript)

### FE-01 · Preparar o frontend para integração `[M0][frontend][chore][M]`
- [ ] Migrar protótipo para `apps/web`; dividir `App.tsx` (692 linhas) em módulos por funcionalidade (`auth`, `media`, `transcripts`, `templates`, `documents`, `admin`)
- [ ] React Router, TanStack Query, cliente HTTP, tratamento global de erro
- [ ] Remover `localStorage` como fonte de dados e **nunca armazenar senhas**
- [ ] Variáveis via `VITE_*` (somente públicas) — segredos jamais no front
- [ ] ESLint/oxlint, Prettier/oxfmt, Vitest e Testing Library

### FE-02 · Design system e acessibilidade `[M1][frontend][feature][M]`
Cobre RNF-10, RNF-11.
- [ ] Componentes base (botão, formulário, tabela, modal, toast, upload)
- [ ] Contraste, foco por teclado, rótulos ARIA, navegação por leitor de tela (WCAG 2.1 AA)
- [ ] Layout responsivo

### FE-03 · Cliente de API tipado `[M1][frontend][chore][S]`
Depende de BE-23. Gerar cliente TS a partir do OpenAPI (`orval`/`openapi-typescript`) e automatizar no CI.

### FE-04 · Cadastro de instituição, login e recuperação de senha `[M1][frontend][feature][M]`
Cobre RF-01, RF-02. Depende de BE-04, BE-05.
- [ ] Fluxos de cadastro, login, esqueci/redefinir senha
- [ ] Renovação de sessão e redirecionamento ao expirar
- [ ] Rotas protegidas por perfil

### FE-05 · Gestão de usuários (administrador) `[M1][frontend][feature][M]`
Cobre RF-03. Depende de BE-06.

### FE-06 · Upload de mídia (até 10 GB) `[M1][frontend][feature][L]`
Cobre RF-05, RN-05. Depende de BE-08.
- [ ] Upload multipart por partes, com paralelismo limitado, **retomada** após queda e botão de cancelar
- [ ] Barra de progresso, velocidade e tempo restante
- [ ] Validação do limite de 10 GB e dos formatos antes de enviar
- [ ] Testar com arquivo grande e com perda de conexão

### FE-07 · Biblioteca de mídias `[M1][frontend][feature][M]`
Cobre RF-07, RF-09. Lista, filtros, status do processamento em tempo real (SSE/polling), pré-visualização, download e exclusão.

### FE-08 · Solicitar e acompanhar transcrição `[M2][frontend][feature][M]`
Cobre RF-09, RF-10. Depende de BE-11.

### FE-09 · Editor de transcrição com player sincronizado `[M2][frontend][feature][L]`
Cobre RF-11, RF-12, RF-14. Depende de BE-12.
- [ ] Clique no trecho leva ao instante no vídeo; destaque do trecho atual
- [ ] Edição de texto e troca de falante; renomear falantes com propagação
- [ ] Marcar trechos de baixa confiança
- [ ] Virtualização da lista para transcrições longas
- [ ] Exportação (TXT/DOCX/SRT)

### FE-10 · Compressão de vídeo `[M4][frontend][feature][M]`
Cobre RF-08, RN-18. Seleção de perfil, progresso, comparativo antes/depois e download.

### FE-11 · Biblioteca de modelos `[M3][frontend][feature][L]`
Cobre RF-15, RF-16. Depende de BE-13.
- [ ] Lista, criação/edição de modelos e campos, versões e ativação
- [ ] Pré-visualização do modelo

### FE-12 · Assistente de geração de documento `[M3][frontend][feature][L]`
Cobre RF-18, RF-19, RF-20. Depende de BE-14.
- [ ] Passos: escolher modelo → escolher transcrição(ões) → informações extras → gerar
- [ ] Tela de revisão de campos com valor, evidência clicável (leva ao trecho da transcrição) e confiança
- [ ] Destaque dos campos pendentes/ambíguos e formulário para completar

### FE-13 · Editor de documento, versões e revisão automática `[M3][frontend][feature][L]`
Cobre RF-21, RF-22, RF-26. Depende de BE-15, BE-17.
- [ ] Edição, regeneração de seção, sugestões da revisão automática aplicáveis com um clique
- [ ] Histórico de versões com comparação e restauração

### FE-14 · Fluxo de validação e exportação `[M3][frontend][feature][M]`
Cobre RF-23, RF-24, RF-25. Depende de BE-16, BE-18.
- [ ] Enviar para validação, aprovar, devolver com justificativa (validação realizada pelo solicitante, seja Administrador ou Funcionário)
- [ ] Mensagens claras de bloqueio (campos obrigatórios pendentes)
- [ ] Exportar DOCX/PDF

### FE-15 · Dashboard, busca e auditoria `[M3][frontend][feature][M]`
Cobre RF-27, RF-28, RF-29. Dashboard real, busca/filtros globais e tela de auditoria do administrador.

### FE-16 · Configurações da instituição, cotas e privacidade `[M4][frontend][feature][M]`
Cobre RF-30, RN-14, RN-15, RN-16. Retenção, provedores de IA habilitados, consumo e solicitações de titulares.

### FE-17 · Testes end-to-end `[M4][frontend][test][M]`
Playwright cobrindo o fluxo principal: cadastro → upload → transcrição → geração → validação → exportação (usando provedores fake).

---

# Resumo

| Área | Issues | Marcos principais |
|---|---|---|
| Documentação | 15 | ADRs e modelo de domínio em M0 |
| Infraestrutura | 21 | HCP Terraform, Infisical e servidor em M0–M1 |
| Backend | 24 | Auth e upload em M1, documentos em M3 |
| Workers | 11 | Transcrição em M2, IA de documentos em M3 |
| Frontend | 17 | Upload e auth em M1, editor em M2–M3 |
| **Total** | **88** | |

## Caminho crítico recomendado (primeiras duas semanas)
1. **Todos:** DOC-01, DOC-06 (spike do provedor de IA — destrava workers), DOC-08, DOC-10.
2. **C (infra):** INF-01 → INF-02 → INF-03/04 → INF-05 → INF-19 (agent) → INF-06 → INF-20 → INF-08 → INF-09.
3. **A (back/workers):** BE-01, BE-02, BE-03 → BE-04/05 → WK-01.
4. **B (front):** FE-01, FE-02, FE-03 → FE-04.

> [!TIP]
> Entregue uma **fatia vertical mínima o quanto antes**: upload → transcrição com falantes → ata gerada → exportação, mesmo com UI simples. Compressão, cotas e observabilidade completas podem esperar.
