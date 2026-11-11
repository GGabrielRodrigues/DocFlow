output "grafana_container_name" {
  value       = module.grafana.grafana_container_name
  description = "Name of the Grafana Docker container"
}

output "grafana_port" {
  value       = module.grafana.grafana_port
  description = "External port of the Grafana service"
}

output "alloy_container_name" {
  value       = module.grafana_alloy.alloy_container_name
  description = "Name of the Grafana Alloy Docker container"
}
