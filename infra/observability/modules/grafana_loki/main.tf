data "docker_network" "shared" {
  name = "shared-network"
}

resource "docker_image" "loki" {
  name         = "grafana/loki:${var.loki_image_tag}"
  keep_locally = true
}

resource "docker_volume" "loki_data" {
  name = "grafana-loki-data"
}

resource "docker_container" "loki" {
  name    = "grafana-loki"
  image   = docker_image.loki.image_id
  restart = "always"

  env = [
    "LOKI_S3_ACCESS_KEY=${var.loki_s3_access_key}",
    "LOKI_S3_SECRET_KEY=${var.loki_s3_secret_key}",
    "LOKI_S3_ENDPOINT=${var.loki_s3_endpoint}",
    "LOKI_S3_BUCKET=${var.loki_s3_bucket}",
    "LOKI_RETENTION_PERIOD=${var.loki_retention_period}"
  ]

  ports {
    internal = 3100
    external = var.loki_port
  }

  volumes {
    volume_name    = docker_volume.loki_data.name
    container_path = "/loki"
  }

  upload {
    content = templatefile("${path.module}/files/loki-config.yaml", {
      s3_endpoint      = var.loki_s3_endpoint
      s3_bucket        = var.loki_s3_bucket
      s3_access_key    = var.loki_s3_access_key
      s3_secret_key    = var.loki_s3_secret_key # gitleaks:allow
      retention_period = var.loki_retention_period
    })
    file = "/etc/loki/local-config.yaml"
  }

  command = ["-config.file=/etc/loki/local-config.yaml"]

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
