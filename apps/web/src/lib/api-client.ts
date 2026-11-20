import type {
  AuditLogItemResponse,
  ForgotPasswordRequest,
  LivenessResponse,
  LoginRequest,
  LogoutRequest,
  MeResponse,
  MessageResponse,
  PaginatedAuditLogsResponse,
  ReadinessResponse,
  RecordAuditLogRequest,
  RefreshRequest,
  RegistrationRequest,
  RegistrationResponse,
  ResetPasswordRequest,
  TokenResponse,
  operations,
  paths,
} from "./api-schema.gen"
import { type HttpRequestOptions, httpRequest } from "./http-client"

export type ApiPath = keyof paths

export type HttpMethod = "get" | "post" | "put" | "patch" | "delete"

export type PathMethods<P extends ApiPath> = Extract<keyof paths[P], HttpMethod>

export type OperationFor<
  P extends ApiPath,
  M extends PathMethods<P>,
> = paths[P][M]

export type ExtractJsonSuccess<Op> = Op extends {
  responses: infer R
}
  ? "200" extends keyof R
    ? R["200"] extends { content: { "application/json": infer T200 } }
      ? T200
      : void
    : "201" extends keyof R
      ? R["201"] extends { content: { "application/json": infer T201 } }
        ? T201
        : void
      : "202" extends keyof R
        ? R["202"] extends { content: { "application/json": infer T202 } }
          ? T202
          : void
        : void
  : void

export type ExtractRequestBody<Op> = Op extends {
  requestBody: { content: { "application/json": infer B } }
}
  ? B
  : Op extends {
        requestBody?: { content: { "application/json": infer BOpt } }
      }
    ? BOpt | undefined
    : undefined

export interface TypedRequestInit<Op> {
  pathParams?: Op extends { parameters: { path: infer P } }
    ? P
    : Record<string, string | number>
  query?: Op extends { parameters: { query?: infer Q } }
    ? Q
    : Record<string, string | number | boolean | null | undefined>
  headers?: Record<string, string>
  body?: ExtractRequestBody<Op>
  signal?: AbortSignal
}

function interpolatePath(
  template: string,
  pathParams?: Record<string, unknown>,
): string {
  if (!pathParams) return template
  return template.replace(/\{([^}]+)\}/g, (_, key: string) => {
    const val = pathParams[key]
    if (val === undefined || val === null) {
      throw new Error(`Parâmetro de rota obrigatório ausente: {${key}}`)
    }
    return encodeURIComponent(String(val))
  })
}

function normalizeQueryParams(
  query?: Record<string, unknown>,
): Record<string, string | number | boolean | undefined> | undefined {
  if (!query) return undefined
  const cleaned: Record<string, string | number | boolean | undefined> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) {
      cleaned[key] = value as string | number | boolean
    }
  }
  return cleaned
}

/**
 * Executa uma chamada HTTP tipada garantida pelo contrato `contracts/openapi.json` (FE-03).
 */
export async function openapiRequest<
  P extends ApiPath,
  M extends PathMethods<P>,
>(
  path: P,
  method: M,
  init: TypedRequestInit<OperationFor<P, M>> = {},
): Promise<ExtractJsonSuccess<OperationFor<P, M>>> {
  const resolvedPath = interpolatePath(
    path,
    init.pathParams as Record<string, unknown> | undefined,
  )
  const options: HttpRequestOptions = {
    method: method.toUpperCase(),
    params: normalizeQueryParams(
      init.query as Record<string, unknown> | undefined,
    ),
    headers: init.headers,
    body: init.body,
    signal: init.signal,
  }
  return httpRequest<ExtractJsonSuccess<OperationFor<P, M>>>(
    resolvedPath,
    options,
  )
}

export type AuditListQuery = NonNullable<
  operations["list_audit_logs_api_v1_audit_get"]["parameters"]["query"]
>

/**
 * Cliente de API de alto nível tipado a partir do esquema OpenAPI (`contracts/openapi.json`).
 */
export const docflowTypedApi = {
  health: {
    checkLiveness: (): Promise<LivenessResponse> =>
      openapiRequest("/health", "get"),
    checkReadiness: (): Promise<ReadinessResponse> =>
      openapiRequest("/ready", "get"),
  },
  identity: {
    registerInstitution: (
      body: RegistrationRequest,
    ): Promise<RegistrationResponse> =>
      openapiRequest("/api/v1/institutions/register", "post", { body }),
  },
  auth: {
    login: (body: LoginRequest): Promise<TokenResponse> =>
      openapiRequest("/api/v1/auth/login", "post", { body }),
    refresh: (body: RefreshRequest): Promise<TokenResponse> =>
      openapiRequest("/api/v1/auth/refresh", "post", { body }),
    logout: (body?: LogoutRequest | null): Promise<void> =>
      openapiRequest("/api/v1/auth/logout", "post", { body }),
    forgotPassword: (body: ForgotPasswordRequest): Promise<MessageResponse> =>
      openapiRequest("/api/v1/auth/forgot-password", "post", { body }),
    resetPassword: (body: ResetPasswordRequest): Promise<MessageResponse> =>
      openapiRequest("/api/v1/auth/reset-password", "post", { body }),
    getMe: (): Promise<MeResponse> =>
      openapiRequest("/api/v1/auth/me", "get"),
  },
  audit: {
    listAuditLogs: (
      query?: AuditListQuery,
    ): Promise<PaginatedAuditLogsResponse> =>
      openapiRequest("/api/v1/audit", "get", { query }),
    recordAuditLog: (
      body: RecordAuditLogRequest,
    ): Promise<AuditLogItemResponse> =>
      openapiRequest("/api/v1/audit", "post", { body }),
    getAuditLog: (logId: string): Promise<AuditLogItemResponse> =>
      openapiRequest("/api/v1/audit/{log_id}", "get", {
        pathParams: { log_id: logId },
      }),
  },
}
