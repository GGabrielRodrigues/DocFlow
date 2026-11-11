output "shared_network_name" {
  description = "Nome da rede Docker compartilhada criada pelo domínio databases"
  value       = module.databases_env.shared_network_name
}
