# Grafana Variables
variable "grafana_admin_user" {
  type        = string
  description = "Grafana administrator username"
  sensitive   = true
}

variable "grafana_admin_password" {
  type        = string
  description = "Grafana administrator password"
  sensitive   = true
}

variable "grafana_port" {
  type        = number
  description = "External port mapped to Grafana UI"
  default     = 3000
}

variable "grafana_image_tag" {
  type        = string
  description = "The tag of the grafana/grafana Docker image to use"
  default     = "latest"
}

variable "loki_url" {
  type        = string
  description = "URL for Loki datasource"
  default     = "http://grafana-loki:3100"
}

# Loki Variables
variable "loki_s3_access_key" {
  type        = string
  description = "Access key for Loki S3/Silo storage"
  sensitive   = true
}

variable "loki_s3_secret_key" {
  type        = string
  description = "Secret key for Loki S3/Silo storage"
  sensitive   = true
}

variable "loki_s3_endpoint" {
  type        = string
  description = "S3/Silo endpoint URL for Loki"
}

variable "loki_s3_bucket" {
  type        = string
  description = "S3/Silo bucket name for Loki data"
  default     = "loki-data"
}

variable "loki_port" {
  type        = number
  description = "External port mapped to Loki HTTP API"
  default     = 3100
}

variable "loki_image_tag" {
  type        = string
  description = "The tag of the grafana/loki Docker image to use"
  default     = "latest"
}

variable "loki_retention_period" {
  type        = string
  description = "Log retention period (e.g., 720h for 30 days)"
  default     = "720h"
}

# Grafana Alloy Variables
variable "alloy_image_tag" {
  type        = string
  description = "The tag of the grafana/alloy Docker image to use"
  default     = "v1.7.5"
}

variable "docker_networks_regex" {
  type        = string
  description = "Regex matching Docker network names to scrape logs from"
  default     = "(shared-network)"
}

variable "project_name" {
  type        = string
  description = "Project label value attached to scraped logs"
  default     = "docflow"
}
