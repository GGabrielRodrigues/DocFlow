module "pgadmin" {
  source = "../pgadmin"

  pgadmin_default_email    = var.pgadmin_default_email
  pgadmin_default_password = var.pgadmin_default_password
  pgadmin_port             = var.pgadmin_port
  pgadmin_image_tag        = var.pgadmin_image_tag
}

module "portainer" {
  source = "../portainer"

  portainer_https_port        = var.portainer_https_port
  portainer_tunnel_port       = var.portainer_tunnel_port
  portainer_db_connection_url = var.portainer_db_connection_url
  portainer_license_key       = var.portainer_license_key
}
