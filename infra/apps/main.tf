data "infisical_secrets" "databases_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/databases"
}

data "infisical_secrets" "apps_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/apps"
}

module "apps_env" {
  source = "./modules/env_base"

  # Web (apps/web/Dockerfile)
  web_image_tag = var.web_image_tag != "" ? var.web_image_tag : data.infisical_secrets.apps_secrets.secrets["web_image_tag"].value

  # Server (apps/server/Dockerfile -> API + Workers Celery)
  server_image_tag       = var.server_image_tag != "" ? var.server_image_tag : data.infisical_secrets.apps_secrets.secrets["server_image_tag"].value
  jwt_secret_key         = data.infisical_secrets.apps_secrets.secrets["jwt_secret_key"].value
  cors_allowed_origins   = data.infisical_secrets.apps_secrets.secrets["cors_allowed_origins"].value
  transcription_provider = data.infisical_secrets.apps_secrets.secrets["transcription_provider"].value
  deepgram_api_key       = data.infisical_secrets.apps_secrets.secrets["deepgram_api_key"].value
  llm_provider           = data.infisical_secrets.apps_secrets.secrets["llm_provider"].value
  gemini_api_key         = data.infisical_secrets.apps_secrets.secrets["gemini_api_key"].value

  # Conexões vindas de /databases
  database_url       = "postgresql+psycopg://${data.infisical_secrets.databases_secrets.secrets["postgres_user"].value}:${data.infisical_secrets.databases_secrets.secrets["postgres_password"].value}@postgres:5432/${data.infisical_secrets.databases_secrets.secrets["postgres_db"].value}"
  redis_url          = "redis://default:${data.infisical_secrets.databases_secrets.secrets["redis_password"].value}@redis:${data.infisical_secrets.databases_secrets.secrets["redis_port"].value}/0"
  s3_internal_url    = "http://silo:9000"
  s3_public_endpoint = data.infisical_secrets.databases_secrets.secrets["silo_public_endpoint"].value
  s3_access_key      = data.infisical_secrets.databases_secrets.secrets["silo_docflow_app_user"].value
  s3_secret_key      = data.infisical_secrets.databases_secrets.secrets["silo_docflow_app_password"].value
}
