data "infisical_secrets" "databases_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/databases"
}

module "databases_env" {
  source = "./modules/env_base"

  # Silo (Object Storage S3)
  silo_root_user            = data.infisical_secrets.databases_secrets.secrets["silo_root_user"].value
  silo_root_password        = data.infisical_secrets.databases_secrets.secrets["silo_root_password"].value
  silo_docflow_app_user     = data.infisical_secrets.databases_secrets.secrets["silo_docflow_app_user"].value
  silo_docflow_app_password = data.infisical_secrets.databases_secrets.secrets["silo_docflow_app_password"].value

  # PostgreSQL
  postgres_db       = data.infisical_secrets.databases_secrets.secrets["postgres_db"].value
  postgres_user     = data.infisical_secrets.databases_secrets.secrets["postgres_user"].value
  postgres_password = data.infisical_secrets.databases_secrets.secrets["postgres_password"].value

  # Redis
  redis_password     = data.infisical_secrets.databases_secrets.secrets["redis_password"].value
  redis_port         = tonumber(data.infisical_secrets.databases_secrets.secrets["redis_port"].value)
  redis_memory_limit = tonumber(data.infisical_secrets.databases_secrets.secrets["redis_memory_limit"].value)
  redis_cpu_limit    = tonumber(data.infisical_secrets.databases_secrets.secrets["redis_cpu_limit"].value)
}
