output "grafana_container_name" {
  description = "Name of the Grafana Docker container"
  value       = module.observability_env.grafana_container_name
}

output "grafana_port" {
  description = "External port of the Grafana service"
  value       = module.observability_env.grafana_port
}

output "alloy_container_name" {
  description = "Name of the Grafana Alloy Docker container"
  value       = module.observability_env.alloy_container_name
}
