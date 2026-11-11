resource "docker_image" "postgres" {
  name         = "postgres:16.2-alpine"
  keep_locally = true
}

resource "docker_volume" "postgres_data" {
  name = "postgres-data"
}

resource "docker_container" "postgres" {
  name  = "postgres"
  image = docker_image.postgres.image_id

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  networks_advanced {
    name = var.postgres_network
  }

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}",
  ]

  command = [
    "postgres",
    "-c", "log_connections=on",
    "-c", "log_disconnections=on",
    "-c", "log_min_duration_statement=${var.postgres_log_min_duration_statement}",
    "-c", "log_lock_waits=on",
    "-c", "log_autovacuum_min_duration=${var.postgres_log_autovacuum_min_duration}"
  ]

  ports {
    internal = 5432
    external = 5432
  }

  must_run = true

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }
}
