locals {
  common_env = [
    "DATABASE_URL=${var.database_url}",
    "REDIS_URL=${var.redis_url}",
    "S3_INTERNAL_URL=${var.s3_internal_url}",
    "S3_PUBLIC_ENDPOINT=${var.s3_public_endpoint}",
    "S3_ACCESS_KEY=${var.s3_access_key}",
    "S3_SECRET_KEY=${var.s3_secret_key}",
    "JWT_SECRET_KEY=${var.jwt_secret_key}",
    "CORS_ALLOWED_ORIGINS=${var.cors_allowed_origins}",
    "TRANSCRIPTION_PROVIDER=${var.transcription_provider}",
    "DEEPGRAM_API_KEY=${var.deepgram_api_key}",
    "LLM_PROVIDER=${var.llm_provider}",
    "GEMINI_API_KEY=${var.gemini_api_key}"
  ]
}

# Imagem única gerada por apps/server/Dockerfile (API + Workers Celery)
resource "docker_image" "server" {
  name          = "${var.image_registry}/${var.image_name}:${var.image_tag}"
  keep_locally  = true
  pull_triggers = [var.image_tag]
}

# 1. Contêiner da API HTTP (FastAPI / Uvicorn)
resource "docker_container" "api" {
  name    = "docflow-api"
  image   = docker_image.server.image_id
  restart = "unless-stopped"

  env     = local.common_env
  command = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

  ports {
    internal = 8000
    external = var.api_external_port
  }

  networks_advanced {
    name    = var.network_name
    aliases = ["docflow-api"]
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }
}

# 2. Contêiner Worker I/O (Celery - fila: io)
resource "docker_container" "worker_io" {
  name    = "docflow-worker-io"
  image   = docker_image.server.image_id
  restart = "unless-stopped"

  env     = local.common_env
  command = ["celery", "-A", "app.worker", "worker", "-Q", "io", "--loglevel=info"]

  networks_advanced {
    name = var.network_name
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }
}

# 3. Contêiner Worker CPU (Celery - fila: cpu para FFmpeg e LibreOffice)
resource "docker_container" "worker_cpu" {
  name    = "docflow-worker-cpu"
  image   = docker_image.server.image_id
  restart = "unless-stopped"

  env     = local.common_env
  command = ["celery", "-A", "app.worker", "worker", "-Q", "cpu", "--loglevel=info"]

  memory     = var.worker_cpu_memory_limit
  cpu_shares = var.worker_cpu_shares

  networks_advanced {
    name = var.network_name
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env,
      memory_swap
    ]
  }
}

# 4. Contêiner Worker IA (Celery - fila: ai para Deepgram e Gemini)
resource "docker_container" "worker_ai" {
  name    = "docflow-worker-ai"
  image   = docker_image.server.image_id
  restart = "unless-stopped"

  env     = local.common_env
  command = ["celery", "-A", "app.worker", "worker", "-Q", "ai", "--loglevel=info"]

  networks_advanced {
    name = var.network_name
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }
}
