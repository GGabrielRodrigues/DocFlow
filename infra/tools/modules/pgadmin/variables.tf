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
  description = "External port mapped to pgAdmin (default is 5050)"
  default     = 5050
}

variable "pgadmin_image_tag" {
  type        = string
  description = "The tag of the dpage/pgadmin4 image to use"
  default     = "latest"
}
