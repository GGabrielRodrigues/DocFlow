output "container_name" {
  description = "Nome do contêiner do Portainer"
  value       = docker_container.portainer.name
}
