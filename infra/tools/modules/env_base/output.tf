output "pgadmin_container_name" {
  description = "Nome do contêiner do pgAdmin"
  value       = module.pgadmin.container_name
}

output "portainer_container_name" {
  description = "Nome do contêiner do Portainer"
  value       = module.portainer.container_name
}
