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

variable "postgres_network" {
  type        = string
  description = "Nome da rede Docker à qual o Postgres deve se conectar"
  sensitive   = false
}

variable "postgres_log_min_duration_statement" {
  type        = number
  description = "Duração mínima, em milissegundos, para uma consulta ser registrada no log"
  default     = 1000
}

variable "postgres_log_autovacuum_min_duration" {
  type        = number
  description = "Duração mínima, em milissegundos, para uma ação de autovacuum ser registrada"
  default     = 0
}
