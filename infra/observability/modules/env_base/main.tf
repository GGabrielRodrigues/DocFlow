module "grafana" {
  source = "../grafana"

  grafana_admin_user     = var.grafana_admin_user
  grafana_admin_password = var.grafana_admin_password
  grafana_port           = var.grafana_port
  grafana_image_tag      = var.grafana_image_tag
  loki_url               = var.loki_url
}

module "grafana_alloy" {
  source = "../grafana_alloy"

  alloy_image_tag       = var.alloy_image_tag
  loki_url              = var.loki_url
  docker_networks_regex = var.docker_networks_regex
  project_name          = var.project_name
}

module "grafana_loki" {
  source = "../grafana_loki"

  loki_s3_access_key    = var.loki_s3_access_key
  loki_s3_secret_key    = var.loki_s3_secret_key
  loki_s3_endpoint      = var.loki_s3_endpoint
  loki_s3_bucket        = var.loki_s3_bucket
  loki_port             = var.loki_port
  loki_image_tag        = var.loki_image_tag
  loki_retention_period = var.loki_retention_period
}
