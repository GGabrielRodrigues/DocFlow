output "loki_container_name" {
  description = "Nome do contêiner do Grafana Loki"
  value       = docker_container.loki.name
}
