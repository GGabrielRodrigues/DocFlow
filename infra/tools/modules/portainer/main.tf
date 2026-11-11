data "docker_network" "shared" {
  name = "shared-network"
}

resource "docker_image" "portainer" {
  name         = "portainer/portainer-ee:latest"
  keep_locally = true
}

resource "docker_volume" "portainer_data" {
  name = "portainer-data"
}

resource "docker_container" "portainer" {
  name    = "portainer"
  image   = docker_image.portainer.image_id
  restart = "always"

  env = compact([
    var.portainer_db_connection_url != "" ? "DATABASE_URL=${var.portainer_db_connection_url}" : "",
    var.portainer_license_key != "" ? "PORTAINER_LICENSE_KEY=${var.portainer_license_key}" : ""
  ])

  ports {
    internal = 9000
    external = var.portainer_https_port
  }

  ports {
    internal = 9443
    external = 9443
  }

  ports {
    internal = 8000
    external = var.portainer_tunnel_port
  }

  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
  }

  volumes {
    volume_name    = docker_volume.portainer_data.name
    container_path = "/data"
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
