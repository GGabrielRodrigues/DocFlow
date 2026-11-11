data "docker_network" "shared" {
  name = "shared-network"
}

locals {
  dashboard_files = fileset("${path.module}/files/dashboards", "*.json")

  classic_dashboards = [
    for f in local.dashboard_files : f
    if !can(regex("dashboard\\.grafana\\.app/v2", file("${path.module}/files/dashboards/${f}")))
  ]
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:${var.grafana_image_tag}"
  keep_locally = true
}

resource "docker_volume" "grafana_data" {
  name = "grafana-data"
}

resource "docker_container" "grafana" {
  name    = "grafana"
  image   = docker_image.grafana.image_id
  restart = "always"

  env = [
    "GF_SECURITY_ADMIN_USER=${var.grafana_admin_user}",
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_ALLOW_SIGN_UP=false",
    "LOKI_URL=${var.loki_url}"
  ]

  ports {
    internal = 3000
    external = var.grafana_port
  }

  volumes {
    volume_name    = docker_volume.grafana_data.name
    container_path = "/var/lib/grafana"
  }

  upload {
    content = file("${path.module}/files/provisioning/datasources/datasources.yaml")
    file    = "/etc/grafana/provisioning/datasources/datasources.yaml"
  }

  upload {
    content = file("${path.module}/files/provisioning/dashboards/dashboards.yaml")
    file    = "/etc/grafana/provisioning/dashboards/dashboards.yaml"
  }

  dynamic "upload" {
    for_each = local.classic_dashboards

    content {
      content = file("${path.module}/files/dashboards/${upload.value}")
      file    = "/etc/grafana/dashboards/${upload.value}"
    }
  }

  dynamic "upload" {
    for_each = var.domain_dashboards

    content {
      content = templatefile("${path.module}/files/dashboard-templates/domain-overview.json.tftpl", {
        domain_key      = upload.key
        domain_title    = upload.value.title
        container_regex = upload.value.container_regex
      })
      file = "/etc/grafana/dashboards/domain-${upload.key}.json"
    }
  }

  networks_advanced {
    name = data.docker_network.shared.name
  }

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint
    ]
  }
}
