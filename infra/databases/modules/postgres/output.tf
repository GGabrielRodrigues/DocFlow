output "connection_url" {
  description = "URL de conexão do banco de dados Postgres"
  value       = "postgresql://${var.postgres_user}:${var.postgres_password}@postgres:5432/${var.postgres_db}"
  sensitive   = true
}
