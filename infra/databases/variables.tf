# Infisical Universal Auth
variable "infisical_client_id" {
  type        = string
  description = "Client ID for Infisical Universal Auth"
  sensitive   = true
}

variable "infisical_client_secret" {
  type        = string
  description = "Client Secret for Infisical Universal Auth"
  sensitive   = true
}

variable "infisical_workspace_id" {
  type        = string
  description = "Workspace ID (Project ID) in Infisical"
}

variable "docker_host" {
  type        = string
  description = "Host do daemon Docker. Se vazio, utiliza o valor docker_ssh_host do Infisical"
  default     = ""
}
