variable "alloy_image_tag" {
  type        = string
  description = "The tag of the grafana/alloy Docker image to use"
  default     = "v1.7.5"
}

variable "loki_url" {
  type        = string
  description = "URL for Loki endpoint where logs should be sent"
  default     = "http://grafana-loki:3100"
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
