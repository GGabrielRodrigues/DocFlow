output "container_name" {
  description = "Nome do contêiner do pgAdmin"
  value       = docker_container.pgadmin.name
}
