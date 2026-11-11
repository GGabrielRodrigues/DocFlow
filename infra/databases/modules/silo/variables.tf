variable "silo_network" {
  type        = string
  description = "Nome da rede Docker à qual o Silo deve se conectar"
}

variable "silo_image" {
  type        = string
  description = "Imagem Docker do Silo (S3-compatível, fork do MinIO)"
  default     = "quay.io/minio/minio:latest"
}

variable "external_api_s3_port" {
  type        = number
  description = "External API S3 Port"
  default     = 9000
}

variable "external_console_port" {
  type        = number
  description = "External Console Port"
  default     = 9001
}

variable "silo_root_user" {
  type        = string
  description = "Usuário root do Silo"
  sensitive   = true
}

variable "silo_root_password" {
  type        = string
  description = "Senha root do Silo"
  sensitive   = true
}

variable "silo_docflow_app_user" {
  type        = string
  description = "Access Key da aplicação DocFlow no Silo"
  sensitive   = true
}

variable "silo_docflow_app_password" {
  type        = string
  description = "Secret Key da aplicação DocFlow no Silo"
  sensitive   = true
}
