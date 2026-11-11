data "docker_network" "shared" {
  name = "shared-network"
}

module "web" {
  source = "../web"

  image_tag    = var.web_image_tag
  network_name = data.docker_network.shared.name
}

module "server" {
  source = "../server"

  image_tag              = var.server_image_tag
  network_name           = data.docker_network.shared.name
  database_url           = var.database_url
  redis_url              = var.redis_url
  s3_internal_url        = var.s3_internal_url
  s3_public_endpoint     = var.s3_public_endpoint
  s3_access_key          = var.s3_access_key
  s3_secret_key          = var.s3_secret_key
  jwt_secret_key         = var.jwt_secret_key
  cors_allowed_origins   = var.cors_allowed_origins
  transcription_provider = var.transcription_provider
  deepgram_api_key       = var.deepgram_api_key
  llm_provider           = var.llm_provider
  gemini_api_key         = var.gemini_api_key
}
