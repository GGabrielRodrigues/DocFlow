output "container_name" {
  description = "Nome do contêiner do frontend web"
  value       = docker_container.web.name
}
