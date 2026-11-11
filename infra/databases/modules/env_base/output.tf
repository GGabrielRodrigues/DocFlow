output "shared_network_name" {
  description = "Nome da rede Docker compartilhada"
  value       = docker_network.shared.name
}

output "postgres_connection_url" {
  description = "URL de conexão do banco de dados Postgres"
  value       = module.postgres.connection_url
  sensitive   = true
}

output "redis_connection_url" {
  description = "URL de conexão do Redis"
  value       = module.redis.redis_connection_url
  sensitive   = true
}
