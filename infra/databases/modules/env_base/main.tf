# Rede Docker global "shared-network"
resource "docker_network" "shared" {
  name   = "shared-network"
  driver = "bridge"
}

module "silo" {
  source = "../silo"

  external_api_s3_port  = 9000
  external_console_port = 9001

  silo_root_user            = var.silo_root_user
  silo_root_password        = var.silo_root_password
  silo_docflow_app_user     = var.silo_docflow_app_user
  silo_docflow_app_password = var.silo_docflow_app_password

  silo_network = docker_network.shared.name
}

module "postgres" {
  source = "../postgres"

  postgres_user     = var.postgres_user
  postgres_password = var.postgres_password
  postgres_db       = var.postgres_db
  postgres_network  = docker_network.shared.name
}

module "redis" {
  source = "../redis"

  redis_password     = var.redis_password
  redis_memory_limit = var.redis_memory_limit
  redis_cpu_limit    = var.redis_cpu_limit
  redis_port         = var.redis_port
  container_name     = "redis"
  redis_network      = docker_network.shared.name
}
