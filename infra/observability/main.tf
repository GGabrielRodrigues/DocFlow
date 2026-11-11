data "infisical_secrets" "databases_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/databases"
}

data "infisical_secrets" "observability_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/observability"
}

module "observability_env" {
  source = "./modules/env_base"

  # Grafana (Infisical secrets em /observability)
  grafana_admin_user     = data.infisical_secrets.observability_secrets.secrets["grafana_admin_user"].value
  grafana_admin_password = data.infisical_secrets.observability_secrets.secrets["grafana_admin_password"].value
  grafana_port           = tonumber(data.infisical_secrets.observability_secrets.secrets["grafana_port"].value)
  loki_url               = "http://grafana-loki:${data.infisical_secrets.observability_secrets.secrets["loki_port"].value}"

  # Loki (Infisical secrets em /observability — storage S3 no Silo)
  loki_s3_access_key = data.infisical_secrets.observability_secrets.secrets["silo_loki_user"].value
  loki_s3_secret_key = data.infisical_secrets.observability_secrets.secrets["silo_loki_password"].value
  loki_s3_endpoint   = data.infisical_secrets.observability_secrets.secrets["silo_internal_url"].value
  loki_s3_bucket     = data.infisical_secrets.observability_secrets.secrets["silo_loki_bucket"].value
  loki_port          = tonumber(data.infisical_secrets.observability_secrets.secrets["loki_port"].value)
}
