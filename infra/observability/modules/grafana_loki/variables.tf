variable "loki_s3_access_key" {
  type        = string
  description = "Access key for S3/Silo storage backend"
  sensitive   = true
}

variable "loki_s3_secret_key" {
  type        = string
  description = "Secret key for S3/Silo storage backend"
  sensitive   = true
}

variable "loki_s3_endpoint" {
  type        = string
  description = "S3/Silo endpoint URL"
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
