output "pgadmin_container_name" {
  description = "Nome do contêiner do pgAdmin"
  value       = module.tools_env.pgadmin_container_name
}

output "portainer_container_name" {
  description = "Nome do contêiner do Portainer"
  value       = module.tools_env.portainer_container_name
}
