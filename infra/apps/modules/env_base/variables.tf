variable "web_image_tag" {
  type        = string
  description = "Tag da imagem Docker do frontend (docflow-web)"
  default     = "latest"
}

variable "server_image_tag" {
  type        = string
  description = "Tag da imagem Docker única do backend e workers (docflow-server)"
  default     = "latest"
}

variable "database_url" {
  type        = string
  description = "URL de conexão ao PostgreSQL"
  sensitive   = true
}

variable "redis_url" {
  type        = string
  description = "URL de conexão ao Redis"
  sensitive   = true
}

variable "s3_internal_url" {
  type        = string
  description = "Endpoint interno S3 do Silo"
  default     = "http://silo:9000"
}

variable "s3_public_endpoint" {
  type        = string
  description = "Endpoint público HTTPS do Silo via Cloudflare Tunnel"
}

variable "s3_access_key" {
  type        = string
  description = "Access Key do Silo"
  sensitive   = true
}

variable "s3_secret_key" {
  type        = string
  description = "Secret Key do Silo"
  sensitive   = true
}

variable "jwt_secret_key" {
  type        = string
  description = "Chave secreta para assinatura de tokens JWT"
  sensitive   = true
}

variable "cors_allowed_origins" {
  type        = string
  description = "Origens permitidas no CORS da API"
}

variable "transcription_provider" {
  type        = string
  description = "Provedor de transcrição ativo (deepgram, assemblyai, google_stt, fake)"
  default     = "deepgram"
}

variable "deepgram_api_key" {
  type        = string
  description = "Chave de API do Deepgram"
  sensitive   = true
}

variable "llm_provider" {
  type        = string
  description = "Provedor de LLM ativo (gemini, openai, fake)"
  default     = "gemini"
}

variable "gemini_api_key" {
  type        = string
  description = "Chave de API do Google Gemini"
  sensitive   = true
}
