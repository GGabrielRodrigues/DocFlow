data "docker_network" "shared" {
  name = "shared-network"
}

resource "docker_image" "alloy" {
  name         = "grafana/alloy:${var.alloy_image_tag}"
  keep_locally = true
}

resource "docker_volume" "alloy_data" {
  name = "grafana-alloy-data"
}

resource "docker_container" "alloy" {
  name    = "grafana-alloy"
  image   = docker_image.alloy.image_id
  restart = "always"

  volumes {
    host_path      = "/var/run/docker.sock"
    container_path = "/var/run/docker.sock"
  }

  volumes {
    volume_name    = docker_volume.alloy_data.name
    container_path = "/var/lib/alloy/data"
  }

  upload {
    content = templatefile("${path.module}/files/config.alloy", {
      loki_url              = var.loki_url
      docker_networks_regex = var.docker_networks_regex
      project_name          = var.project_name
    })
    file = "/etc/alloy/config.alloy"
  }

  command = [
    "run",
    "--server.http.listen-addr=0.0.0.0:12345",
    "--storage.path=/var/lib/alloy/data",
    "/etc/alloy/config.alloy"
  ]

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
