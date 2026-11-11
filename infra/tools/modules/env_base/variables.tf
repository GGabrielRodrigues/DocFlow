variable "pgadmin_default_email" {
  type        = string
  description = "Default email for pgAdmin initial administrator account"
  sensitive   = true
}

variable "pgadmin_default_password" {
  type        = string
  description = "Default password for pgAdmin initial administrator account"
  sensitive   = true
}

variable "pgadmin_port" {
  type        = number
  description = "External port mapped to pgAdmin"
  default     = 5050
}

variable "pgadmin_image_tag" {
  type        = string
  description = "The tag of the dpage/pgadmin4 image to use"
  default     = "latest"
}

variable "portainer_https_port" {
  type        = number
  description = "External port for Portainer UI"
  default     = 9443
}

variable "portainer_tunnel_port" {
  type        = number
  description = "External port for Portainer Edge Agent tunnel"
  default     = 8000
}

variable "portainer_db_connection_url" {
  type        = string
  description = "Database connection URL for Portainer"
  sensitive   = true
  default     = ""
}

variable "portainer_license_key" {
  type        = string
  description = "Portainer Business Edition license key"
  sensitive   = true
  default     = ""
}
