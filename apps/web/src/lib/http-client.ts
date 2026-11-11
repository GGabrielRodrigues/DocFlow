import { env } from './env'

export interface FieldValidationError {
  field: string
  code: string
  message: string
}

/**
 * RFC 9457 Problem Details payload returned by the DocFlow API (`contracts/docs/contrato-api.md`).
 */
export interface ProblemDetails {
  type: string
  title: string
  status: number
  detail?: string
  instance?: string
  request_id?: string
  errors?: FieldValidationError[]
}

export class ApiProblemError extends Error {
  readonly type: string
  readonly title: string
  readonly status: number
  readonly detail?: string
  readonly instance?: string
  readonly requestId?: string
  readonly errors: FieldValidationError[]

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title || 'Erro ao comunicar com o servidor.')
    this.name = 'ApiProblemError'
    this.type = problem.type
    this.title = problem.title
    this.status = problem.status
    this.detail = problem.detail
    this.instance = problem.instance
    this.requestId = problem.request_id
    this.errors = problem.errors ?? []
  }
}

export interface HttpRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  params?: Record<string, string | number | boolean | undefined>
}

export type ErrorListener = (error: ApiProblemError) => void

let inMemoryAccessToken: string | null = null
const errorListeners = new Set<ErrorListener>()

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken
}

export function onGlobalApiError(listener: ErrorListener): () => void {
  errorListeners.add(listener)
  return () => {
    errorListeners.delete(listener)
  }
}

export function notifyGlobalApiError(error: ApiProblemError): void {
  for (const listener of errorListeners) {
    listener(error)
  }
}

function buildUrl(
  baseUrl: string,
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = new URL(`${baseUrl}${normalizedPath}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }
  return url.toString()
}

export async function httpRequest<T>(path: string, options: HttpRequestOptions = {}): Promise<T> {
  const { body, params, headers: customHeaders, ...rest } = options
  const requestId = crypto.randomUUID()
  const headers = new Headers(customHeaders)

  headers.set('Accept', 'application/json, application/problem+json')
  headers.set('X-Request-ID', requestId)

  if (inMemoryAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${inMemoryAccessToken}`)
  }

  let serializedBody: BodyInit | undefined
  if (body !== undefined) {
    if (body instanceof FormData || body instanceof Blob || typeof body === 'string') {
      serializedBody = body
    } else {
      headers.set('Content-Type', 'application/json; charset=utf-8')
      serializedBody = JSON.stringify(body)
    }
  }

  let response: Response
  try {
    response = await fetch(buildUrl(env.apiBaseUrl, path, params), {
      ...rest,
      headers,
      body: serializedBody,
    })
  } catch {
    const networkError = new ApiProblemError({
      type: 'https://api.docflow.com.br/errors/network-error',
      title: 'Falha de conexão com a API',
      status: 0,
      detail: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.',
      request_id: requestId,
    })
    notifyGlobalApiError(networkError)
    throw networkError
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('json')
  const payload = isJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    const problem: ProblemDetails =
      payload && typeof payload === 'object' && 'title' in payload
        ? (payload as ProblemDetails)
        : {
            type: 'https://api.docflow.com.br/errors/http-error',
            title: `Erro HTTP ${response.status}`,
            status: response.status,
            detail:
              payload && typeof payload === 'object' && 'detail' in payload
                ? String((payload as { detail: unknown }).detail)
                : 'Ocorreu um erro inesperado ao processar a solicitação.',
            request_id: response.headers.get('x-request-id') ?? requestId,
          }

    const apiError = new ApiProblemError(problem)
    notifyGlobalApiError(apiError)
    throw apiError
  }

  return payload as T
}

export const httpClient = {
  get: <T>(path: string, options?: Omit<HttpRequestOptions, 'method' | 'body'>) =>
    httpRequest<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<HttpRequestOptions, 'method' | 'body'>) =>
    httpRequest<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<HttpRequestOptions, 'method' | 'body'>) =>
    httpRequest<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<HttpRequestOptions, 'method' | 'body'>) =>
    httpRequest<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<HttpRequestOptions, 'method' | 'body'>) =>
    httpRequest<T>(path, { ...options, method: 'DELETE' }),
}
