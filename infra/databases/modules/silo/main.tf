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
    "MINIO_ROOT_PASSWORD=${var.silo_root_password}"
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

resource "docker_container" "silo_setup" {
  image = "minio/mc"
  name  = "silo_setup"
  count = 0 # Habilite (count = 1) ao provisionar pela primeira vez para criar buckets e usuário da aplicação

  depends_on = [docker_container.silo]

  entrypoint = ["/bin/sh", "-c"]

  command = [
    <<-EOT
      sleep 10;
      mc alias set target http://${docker_container.silo.name}:9000 ${var.silo_root_user} ${var.silo_root_password};
      mc mb --ignore-existing target/media-raw;
      mc mb --ignore-existing target/media-processed;
      mc mb --ignore-existing target/documents;
      mc mb --ignore-existing target/loki-data;
      mc admin user add target ${var.silo_docflow_app_user} ${var.silo_docflow_app_password};
      mc admin policy attach target readwrite --user ${var.silo_docflow_app_user};
    EOT
  ]

  networks_advanced {
    name = var.silo_network
  }
}
