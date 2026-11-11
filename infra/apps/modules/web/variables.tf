variable "image_registry" {
  type        = string
  description = "Registry da imagem Docker"
  default     = "ghcr.io"
}

variable "image_name" {
  type        = string
  description = "Nome da imagem Docker do frontend (apps/web/Dockerfile)"
  default     = "docflow/docflow-web"
}

variable "image_tag" {
  type        = string
  description = "Tag da imagem Docker"
  default     = "latest"
}

variable "web_external_port" {
  type        = number
  description = "Porta externa mapeada para o frontend web"
  default     = 8080
}

variable "network_name" {
  type        = string
  description = "Nome da rede Docker compartilhada"
  default     = "shared-network"
}
