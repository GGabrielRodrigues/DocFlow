output "web_container_name" {
  description = "Nome do contêiner do frontend"
  value       = module.web.container_name
}

output "api_container_name" {
  description = "Nome do contêiner da API"
  value       = module.server.api_container_name
}
