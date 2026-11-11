variable "container_name" {
  type        = string
  description = "Nome do contêiner Docker"
  default     = "shared-redis"
}

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

variable "redis_network" {
  type        = string
  description = "Nome da rede Docker à qual o Redis deve se conectar"
}
