output "silo_endpoint" {
  description = "Endpoint interno S3 do Silo na shared-network"
  value       = "http://${docker_container.silo.name}:9000"
}
