data "docker_network" "shared" {
  name = "shared-network"
}

resource "docker_image" "pgadmin" {
  name         = "dpage/pgadmin4:${var.pgadmin_image_tag}"
  keep_locally = true
}

resource "docker_volume" "pgadmin_data" {
  name = "pgadmin-data"
}

resource "docker_container" "pgadmin" {
  name    = "pgadmin"
  image   = docker_image.pgadmin.image_id
  restart = "always"

  env = [
    "PGADMIN_DEFAULT_EMAIL=${var.pgadmin_default_email}",
    "PGADMIN_DEFAULT_PASSWORD=${var.pgadmin_default_password}",
    "PGADMIN_DISABLE_POSTFIX=true"
  ]

  ports {
    internal = 80
    external = var.pgadmin_port
  }

  volumes {
    volume_name    = docker_volume.pgadmin_data.name
    container_path = "/var/lib/pgadmin"
  }

  networks_advanced {
    name = data.docker_network.shared.name
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }
}
