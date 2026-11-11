export type AppEnvironment = 'development' | 'staging' | 'production' | 'test'

export interface PublicEnvConfig {
  readonly apiBaseUrl: string
  readonly appEnv: AppEnvironment
}

const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

function normalizeBaseUrl(rawUrl: string | undefined): string {
  const trimmed = rawUrl?.trim()
  if (!trimmed) return DEFAULT_API_BASE_URL
  return trimmed.replace(/\/+$/, '')
}

function normalizeAppEnv(rawEnv: string | undefined): AppEnvironment {
  if (rawEnv === 'production' || rawEnv === 'staging' || rawEnv === 'test') {
    return rawEnv
  }
  return 'development'
}

export function createPublicEnv(
  source: Record<string, string | undefined> = import.meta.env as Record<string, string | undefined>,
): PublicEnvConfig {
  return Object.freeze({
    apiBaseUrl: normalizeBaseUrl(source.VITE_API_BASE_URL),
    appEnv: normalizeAppEnv(source.VITE_APP_ENV || source.MODE),
  })
}

export const env: PublicEnvConfig = createPublicEnv()
