terraform {
  required_version = ">= 1.8.0"

  cloud {
    organization = "DocFlow"

    workspaces {
      name = "apps"
    }
  }

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.16.0"
    }
  }
}

provider "docker" {
  host = var.docker_host != "" ? var.docker_host : data.infisical_secrets.databases_secrets.secrets["docker_ssh_host"].value

  registry_auth {
    address  = "ghcr.io"
    username = data.infisical_secrets.databases_secrets.secrets["ghcr_username"].value
    password = data.infisical_secrets.databases_secrets.secrets["ghcr_token"].value # gitleaks:allow
  }
}

provider "infisical" {
  host          = "https://app.infisical.com"
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
}
