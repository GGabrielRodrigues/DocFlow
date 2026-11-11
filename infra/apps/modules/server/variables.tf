variable "image_registry" {
  type        = string
  description = "Registry da imagem Docker"
  default     = "ghcr.io"
}

variable "image_name" {
  type        = string
  description = "Nome da imagem Docker única do servidor (apps/server/Dockerfile)"
  default     = "ggabrielrodrigues/docflow-server"
}

variable "image_tag" {
  type        = string
  description = "Tag da imagem Docker"
  default     = "latest"
}

variable "api_external_port" {
  type        = number
  description = "Porta externa mapeada para a API FastAPI"
  default     = 8000
}

variable "network_name" {
  type        = string
  description = "Nome da rede Docker compartilhada"
  default     = "shared-network"
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
  description = "Provedor de transcrição ativo"
  default     = "deepgram"
}

variable "deepgram_api_key" {
  type        = string
  description = "Chave de API do Deepgram"
  sensitive   = true
}

variable "llm_provider" {
  type        = string
  description = "Provedor de LLM ativo"
  default     = "gemini"
}

variable "gemini_api_key" {
  type        = string
  description = "Chave de API do Google Gemini"
  sensitive   = true
}

variable "worker_cpu_memory_limit" {
  type        = number
  description = "Limite de memória RAM (em MB) do worker CPU (FFmpeg/LibreOffice)"
  default     = 2048
}

variable "worker_cpu_shares" {
  type        = number
  description = "Quota de CPU do worker CPU"
  default     = 1024
}
