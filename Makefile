# =============================================================================
# DocFlow Monorepo — Makefile de Desenvolvimento Local e Qualidade
# =============================================================================

COMPOSE_DEV := docker compose -f docker-compose.dev.yml --env-file .env

.PHONY: help env up down restart ps logs clean web-install web-dev web-build test infra-check

help:
	@echo "Comandos disponíveis no monorepo DocFlow:"
	@echo ""
	@echo "  make env          Cria o arquivo .env local a partir do .env.example (se não existir)"
	@echo "  make up           Sobe os serviços locais de apoio (Postgres, Redis, Silo e Mailpit)"
	@echo "  make down         Para e remove os containers de desenvolvimento local"
	@echo "  make restart      Reinicia os serviços de desenvolvimento local"
	@echo "  make ps           Lista o status dos containers de desenvolvimento local"
	@echo "  make logs         Acompanha os logs dos containers de desenvolvimento local"
	@echo "  make clean        Para os containers locais e apaga os volumes de dados (-v)"
	@echo "  make web-dev      Inicia o servidor de desenvolvimento do frontend (apps/web)"
	@echo "  make web-build    Executa o build de produção do frontend (apps/web)"
	@echo "  make test         Executa a suíte de testes disponível nos módulos"
	@echo "  make infra-check  Executa a esteira DevSecOps da infraestrutura (infra/Makefile)"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Arquivo .env criado a partir de .env.example."; \
	else \
		echo "Arquivo .env já existe."; \
	fi

up: env
	$(COMPOSE_DEV) up -d
	@echo ""
	@echo "Ambiente local iniciado com sucesso!"
	@echo "  - PostgreSQL : localhost:5432"
	@echo "  - Redis      : localhost:6379"
	@echo "  - Silo S3 API: http://localhost:9000"
	@echo "  - Silo UI    : http://localhost:9001"
	@echo "  - Mailpit UI : http://localhost:8025 (SMTP: localhost:1025)"

down:
	$(COMPOSE_DEV) down

restart: down up

ps:
	$(COMPOSE_DEV) ps

logs:
	$(COMPOSE_DEV) logs -f

clean:
	$(COMPOSE_DEV) down -v

web-install:
	npm --prefix apps/web install

web-dev:
	npm --prefix apps/web run dev

web-build:
	npm --prefix apps/web run build

test: web-build
	@if [ -f apps/server/pyproject.toml ]; then \
		echo "Executando testes do backend (apps/server)..."; \
		cd apps/server && uv run pytest; \
	else \
		echo "Backend (apps/server) ainda não inicializado (BE-01). Build do frontend validado!"; \
	fi

infra-check:
	$(MAKE) -C infra check
