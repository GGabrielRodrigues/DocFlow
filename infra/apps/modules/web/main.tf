resource "docker_image" "web" {
  name          = "${var.image_registry}/${var.image_name}:${var.image_tag}"
  keep_locally  = true
  pull_triggers = [var.image_tag]
}

resource "docker_container" "web" {
  name    = "docflow-web"
  image   = docker_image.web.image_id
  restart = "unless-stopped"

  ports {
    internal = 80
    external = var.web_external_port
  }

  networks_advanced {
    name    = var.network_name
    aliases = ["docflow-web"]
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
