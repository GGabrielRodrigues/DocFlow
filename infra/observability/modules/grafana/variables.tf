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
  description = "URL for Loki datasource used in Grafana provisioning"
  default     = "http://grafana-loki:3100"
}

variable "domain_dashboards" {
  type = map(object({
    title           = string
    container_regex = string
  }))
  description = "Dashboards de domínio renderizados a partir de files/dashboard-templates/domain-overview.json.tftpl"

  default = {
    databases = {
      title           = "Databases"
      container_regex = "postgres|shared-redis|silo|silo_setup"
    }
    apps = {
      title           = "Apps (DocFlow)"
      container_regex = "docflow-web|docflow-api|docflow-worker-io|docflow-worker-cpu|docflow-worker-ai"
    }
    tools = {
      title           = "Tools"
      container_regex = "pgadmin|portainer"
    }
    observability = {
      title           = "Observability"
      container_regex = "grafana|grafana-loki|grafana-alloy"
    }
  }
}
