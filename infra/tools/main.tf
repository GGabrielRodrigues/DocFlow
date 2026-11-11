data "infisical_secrets" "databases_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/databases"
}

data "infisical_secrets" "tools_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/tools"
}

module "tools_env" {
  source = "./modules/env_base"

  # pgAdmin
  pgadmin_default_email    = data.infisical_secrets.tools_secrets.secrets["pgadmin_default_email"].value
  pgadmin_default_password = data.infisical_secrets.tools_secrets.secrets["pgadmin_default_password"].value
  pgadmin_port             = tonumber(data.infisical_secrets.tools_secrets.secrets["pgadmin_port"].value)
  pgadmin_image_tag        = data.infisical_secrets.tools_secrets.secrets["pgadmin_image_tag"].value

  # Portainer
  portainer_https_port        = tonumber(data.infisical_secrets.tools_secrets.secrets["portainer_port"].value)
  portainer_tunnel_port       = tonumber(data.infisical_secrets.tools_secrets.secrets["portainer_tunnel_port"].value)
  portainer_db_connection_url = data.infisical_secrets.tools_secrets.secrets["portainer_db_connection_url"].value
  portainer_license_key       = data.infisical_secrets.tools_secrets.secrets["portainer_license_key"].value
}
