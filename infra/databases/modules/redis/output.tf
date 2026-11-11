output "redis_connection_url" {
  description = "URL de conexão do banco de dados Redis"
  value       = "redis://default:${var.redis_password}@${var.container_name}:${var.redis_port}"
  sensitive   = true
}
