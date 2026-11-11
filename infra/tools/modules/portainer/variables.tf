variable "portainer_https_port" {
  type        = number
  description = "Porta externa HTTPS para acesso à interface web do Portainer"
  default     = 9443
}

variable "portainer_tunnel_port" {
  type        = number
  description = "Porta externa para comunicação com Edge Agents"
  default     = 8000
}

variable "portainer_db_connection_url" {
  type        = string
  description = "URL de conexão ao PostgreSQL (opcional)"
  sensitive   = true
  default     = ""
}

variable "portainer_license_key" {
  type        = string
  description = "Chave de licença para o Portainer Business Edition"
  sensitive   = true
  default     = ""
}
