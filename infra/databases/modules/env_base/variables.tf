# Silo (Object Storage S3)
variable "silo_root_user" {
  type        = string
  description = "Usuário root do Silo (S3)"
  sensitive   = true
}

variable "silo_root_password" {
  type        = string
  description = "Senha root do Silo (S3)"
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

variable "silo_console_public_url" {
  type        = string
  description = "URL pública HTTPS da Console Web do Silo"
  default     = ""
}

# Postgres
variable "postgres_user" {
  type        = string
  description = "Usuário do banco Postgres"
  sensitive   = true
}

variable "postgres_password" {
  type        = string
  description = "Senha do banco Postgres"
  sensitive   = true
}

variable "postgres_db" {
  type        = string
  description = "Banco de dados Postgres padrão"
  sensitive   = false
}

# Redis
variable "redis_password" {
  type        = string
  description = "Senha do banco de dados Redis"
  sensitive   = true
}

variable "redis_memory_limit" {
  type        = number
  description = "Limite de memória para o Redis (em MB)"
  default     = 512
}

variable "redis_cpu_limit" {
  type        = number
  description = "Limite de CPU para o Redis"
  default     = 1024
}

variable "redis_port" {
  type        = number
  description = "Porta do banco Redis"
  default     = 6379
}
