locals {
  external_api_s3_port  = var.external_api_s3_port
  external_console_port = var.external_console_port
}

resource "docker_image" "silo_img" {
  name         = var.silo_image
  keep_locally = true
}

resource "docker_volume" "silo_data" {
  name = "silo-data"
}

resource "docker_container" "silo" {
  image = docker_image.silo_img.image_id
  name  = "silo"

  ports {
    internal = 9000
    external = local.external_api_s3_port
  }

  ports {
    internal = 9001
    external = local.external_console_port
  }

  volumes {
    volume_name    = docker_volume.silo_data.name
    container_path = "/data"
  }

  env = compact([
    "MINIO_ROOT_USER=${var.silo_root_user}",
    "MINIO_ROOT_PASSWORD=${var.silo_root_password}",
    "MINIO_API_CORS_ALLOW_ORIGIN=*",
    # URL pública da Console (necessária atrás de proxy reverso/Cloudflare Tunnel)
    var.silo_console_public_url != "" ? "MINIO_BROWSER_REDIRECT_URL=${var.silo_console_public_url}" : ""
  ])

  command = ["server", "/data", "--console-address", ":9001"]
  restart = "always"

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env
    ]
  }

  networks_advanced {
    name = var.silo_network
  }
}

resource "docker_image" "mc_img" {
  name         = "pgsty/mc:latest"
  keep_locally = true
}

resource "docker_container" "silo_setup" {
  image    = docker_image.mc_img.image_id
  name     = "silo_setup"
  must_run = false

  depends_on = [docker_container.silo]

  entrypoint = ["/bin/sh", "-c"]

  command = [
    <<-EOT
      until mc alias set target http://${docker_container.silo.name}:9000 ${var.silo_root_user} ${var.silo_root_password} || mcli alias set target http://${docker_container.silo.name}:9000 ${var.silo_root_user} ${var.silo_root_password}; do
        echo "Aguardando Silo iniciar..."
        sleep 2
      done
      CLI_BIN="mc"
      command -v mc >/dev/null 2>&1 || CLI_BIN="mcli"
      $CLI_BIN mb --ignore-existing target/media-raw
      $CLI_BIN mb --ignore-existing target/media-processed
      $CLI_BIN mb --ignore-existing target/documents
      $CLI_BIN version enable target/documents
      $CLI_BIN mb --ignore-existing target/loki-data
      $CLI_BIN admin user add target ${var.silo_docflow_app_user} ${var.silo_docflow_app_password}
      $CLI_BIN admin policy attach target readwrite --user ${var.silo_docflow_app_user} || true
    EOT
  ]

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env,
      command
    ]
  }

  networks_advanced {
    name = var.silo_network
  }
}
