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

  env = [
    "MINIO_ROOT_USER=${var.silo_root_user}",
    "MINIO_ROOT_PASSWORD=${var.silo_root_password}",
    "MINIO_API_CORS_ALLOW_ORIGIN=*"
  ]

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
      until mcli alias set target http://${docker_container.silo.name}:9000 ${var.silo_root_user} ${var.silo_root_password}; do
        echo "Aguardando Silo iniciar..."
        sleep 2
      done
      mcli mb --ignore-existing target/media-raw
      mcli mb --ignore-existing target/media-processed
      mcli mb --ignore-existing target/documents
      mcli version enable target/documents
      mcli mb --ignore-existing target/loki-data
      mcli admin user add target ${var.silo_docflow_app_user} ${var.silo_docflow_app_password}
      mcli admin policy attach target readwrite --user ${var.silo_docflow_app_user} || true
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
