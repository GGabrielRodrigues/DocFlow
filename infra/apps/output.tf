output "web_container_name" {
  description = "Nome do contêiner do frontend web"
  value       = module.apps_env.web_container_name
}

output "api_container_name" {
  description = "Nome do contêiner da API FastAPI"
  value       = module.apps_env.api_container_name
}
