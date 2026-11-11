resource "docker_image" "redis" {
  name         = "redis:7-alpine"
  keep_locally = true
}

resource "docker_volume" "redis_data" {
  name = "redis-data"
}

resource "docker_container" "redis" {
  name  = var.container_name
  image = docker_image.redis.image_id

  command = ["redis-server", "--appendonly", "yes", "--requirepass", var.redis_password]

  volumes {
    volume_name    = docker_volume.redis_data.name
    container_path = "/data"
  }

  networks_advanced {
    name = var.redis_network
  }

  ports {
    internal = var.redis_port
    external = var.redis_port
  }

  memory     = var.redis_memory_limit
  cpu_shares = var.redis_cpu_limit

  must_run = true

  lifecycle {
    ignore_changes = [
      network_mode,
      entrypoint,
      volumes,
      env,
      memory_swap
    ]
  }
}
