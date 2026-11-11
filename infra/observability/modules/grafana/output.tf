output "grafana_container_name" {
  value       = docker_container.grafana.name
  description = "Name of the Grafana Docker container"
}

output "grafana_port" {
  value       = var.grafana_port
  description = "External port of the Grafana service"
}
