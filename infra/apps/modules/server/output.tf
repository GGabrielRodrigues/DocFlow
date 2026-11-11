output "api_container_name" {
  description = "Nome do contêiner da API FastAPI"
  value       = docker_container.api.name
}
