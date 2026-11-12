// Este arquivo é gerado automaticamente a partir de contracts/openapi.json (FE-03).
// Não edite manualmente. Execute `pnpm --dir apps/web run generate:api` para atualizar.

export interface components {
  schemas: {
    AdministratorRegistrationData: {
      name: string
      email: string
      password: string
    }
    AdministratorResponse: {
      id: string
      institution_id: string
      name: string
      email: string
      role: string
      status: string
    }
    AuditLogItemResponse: {
      id: string
      institution_id: string
      user_id?: string | null
      action: string
      resource_type: string
      resource_id?: string | null
      details?: Record<string, unknown>
      ip_address?: string | null
      created_at: string
    }
    ForgotPasswordRequest: {
      email: string
    }
    HTTPValidationError: {
      detail?: components["schemas"]["ValidationError"][]
    }
    InstitutionMeResponse: {
      id: string
      name: string
      institution_type: string
      cnpj: string
      email: string
      phone?: string | null
      address?: string | null
      created_at: string
    }
    InstitutionRegistrationData: {
      name: string
      institution_type: string
      cnpj: string
      email: string
      phone?: string | null
      address?: string | null
    }
    InstitutionResponse: {
      id: string
      name: string
      institution_type: string
      cnpj: string
      email: string
      phone: string | null
      address: string | null
    }
    LivenessResponse: {
      status: string
      service: string
    }
    LoginRequest: {
      email: string
      password: string
    }
    LogoutRequest: {
      refresh_token?: string | null
    }
    MeResponse: {
      user: components["schemas"]["UserMeResponse"]
      institution: components["schemas"]["InstitutionMeResponse"]
    }
    MessageResponse: {
      message: string
    }
    PaginatedAuditLogsResponse: {
      items: components["schemas"]["AuditLogItemResponse"][]
      total: number
      page: number
      page_size: number
      total_pages: number
    }
    ReadinessResponse: {
      status: string
      checks: Record<string, string>
      request_id: string
    }
    RecordAuditLogRequest: {
      action: string
      resource_type: string
      user_id?: string | null
      resource_id?: string | null
      details?: Record<string, unknown>
      ip_address?: string | null
    }
    RefreshRequest: {
      refresh_token: string
    }
    RegistrationRequest: {
      institution: components["schemas"]["InstitutionRegistrationData"]
      administrator: components["schemas"]["AdministratorRegistrationData"]
    }
    RegistrationResponse: {
      institution: components["schemas"]["InstitutionResponse"]
      administrator: components["schemas"]["AdministratorResponse"]
    }
    ResetPasswordRequest: {
      token: string
      new_password: string
    }
    TokenResponse: {
      access_token: string
      refresh_token: string
      token_type?: string
      expires_in?: number
    }
    UserMeResponse: {
      id: string
      name: string
      email: string
      role: string
      status: string
      institution_id: string
      created_at: string
    }
    ValidationError: {
      loc: (string | number)[]
      msg: string
      type: string
      input?: unknown
      ctx?: Record<string, unknown>
    }
  }
}

export interface operations {
  health_health_get: {
    parameters?: never
    requestBody?: never
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["LivenessResponse"]
        }
      }
    }
  }
  ready_ready_get: {
    parameters?: never
    requestBody?: never
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["ReadinessResponse"]
        }
      }
    }
  }
  register_institution_api_v1_institutions_register_post: {
    parameters?: never
    requestBody: {
      content: {
        "application/json": components["schemas"]["RegistrationRequest"]
      }
    }
    responses: {
      "201": {
        content: {
          "application/json": components["schemas"]["RegistrationResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  list_audit_logs_api_v1_audit_get: {
    parameters: {
      query?: {
        action?: string | null
        resource_type?: string | null
        user_id?: string | null
        start_date?: string | null
        end_date?: string | null
        page?: number
        page_size?: number
        institution_id?: string | null
      }
      header?: {
        "X-Institution-ID"?: string | null
        "X-Tenant-ID"?: string | null
      }
    }
    requestBody?: never
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["PaginatedAuditLogsResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  record_audit_log_api_v1_audit_post: {
    parameters: {
      header?: {
        "X-Institution-ID"?: string | null
        "X-Tenant-ID"?: string | null
      }
    }
    requestBody: {
      content: {
        "application/json": components["schemas"]["RecordAuditLogRequest"]
      }
    }
    responses: {
      "201": {
        content: {
          "application/json": components["schemas"]["AuditLogItemResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  get_audit_log_api_v1_audit__log_id__get: {
    parameters: {
      path: {
        log_id: string
      }
      header?: {
        "X-Institution-ID"?: string | null
        "X-Tenant-ID"?: string | null
      }
    }
    requestBody?: never
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["AuditLogItemResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  login_api_v1_auth_login_post: {
    parameters?: never
    requestBody: {
      content: {
        "application/json": components["schemas"]["LoginRequest"]
      }
    }
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["TokenResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  refresh_api_v1_auth_refresh_post: {
    parameters?: never
    requestBody: {
      content: {
        "application/json": components["schemas"]["RefreshRequest"]
      }
    }
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["TokenResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  logout_api_v1_auth_logout_post: {
    parameters: {
      header?: {
        Authorization?: string | null
      }
    }
    requestBody?: {
      content: {
        "application/json": components["schemas"]["LogoutRequest"] | null
      }
    }
    responses: {
      "204": {
        content?: never
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  forgot_password_api_v1_auth_forgot_password_post: {
    parameters?: never
    requestBody: {
      content: {
        "application/json": components["schemas"]["ForgotPasswordRequest"]
      }
    }
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["MessageResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  reset_password_api_v1_auth_reset_password_post: {
    parameters?: never
    requestBody: {
      content: {
        "application/json": components["schemas"]["ResetPasswordRequest"]
      }
    }
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["MessageResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
  get_me_api_v1_auth_me_get: {
    parameters: {
      header?: {
        Authorization?: string | null
      }
    }
    requestBody?: never
    responses: {
      "200": {
        content: {
          "application/json": components["schemas"]["MeResponse"]
        }
      }
      "422": {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"]
        }
      }
    }
  }
}

export interface paths {
  "/health": {
    get: operations["health_health_get"]
  }
  "/ready": {
    get: operations["ready_ready_get"]
  }
  "/api/v1/institutions/register": {
    post: operations["register_institution_api_v1_institutions_register_post"]
  }
  "/api/v1/audit": {
    get: operations["list_audit_logs_api_v1_audit_get"]
    post: operations["record_audit_log_api_v1_audit_post"]
  }
  "/api/v1/audit/{log_id}": {
    get: operations["get_audit_log_api_v1_audit__log_id__get"]
  }
  "/api/v1/auth/login": {
    post: operations["login_api_v1_auth_login_post"]
  }
  "/api/v1/auth/refresh": {
    post: operations["refresh_api_v1_auth_refresh_post"]
  }
  "/api/v1/auth/logout": {
    post: operations["logout_api_v1_auth_logout_post"]
  }
  "/api/v1/auth/forgot-password": {
    post: operations["forgot_password_api_v1_auth_forgot_password_post"]
  }
  "/api/v1/auth/reset-password": {
    post: operations["reset_password_api_v1_auth_reset_password_post"]
  }
  "/api/v1/auth/me": {
    get: operations["get_me_api_v1_auth_me_get"]
  }
}

export type AdministratorRegistrationData = components["schemas"]["AdministratorRegistrationData"]
export type AdministratorResponse = components["schemas"]["AdministratorResponse"]
export type AuditLogItemResponse = components["schemas"]["AuditLogItemResponse"]
export type ForgotPasswordRequest = components["schemas"]["ForgotPasswordRequest"]
export type HTTPValidationError = components["schemas"]["HTTPValidationError"]
export type InstitutionMeResponse = components["schemas"]["InstitutionMeResponse"]
export type InstitutionRegistrationData = components["schemas"]["InstitutionRegistrationData"]
export type InstitutionResponse = components["schemas"]["InstitutionResponse"]
export type LivenessResponse = components["schemas"]["LivenessResponse"]
export type LoginRequest = components["schemas"]["LoginRequest"]
export type LogoutRequest = components["schemas"]["LogoutRequest"]
export type MeResponse = components["schemas"]["MeResponse"]
export type MessageResponse = components["schemas"]["MessageResponse"]
export type PaginatedAuditLogsResponse = components["schemas"]["PaginatedAuditLogsResponse"]
export type ReadinessResponse = components["schemas"]["ReadinessResponse"]
export type RecordAuditLogRequest = components["schemas"]["RecordAuditLogRequest"]
export type RefreshRequest = components["schemas"]["RefreshRequest"]
export type RegistrationRequest = components["schemas"]["RegistrationRequest"]
export type RegistrationResponse = components["schemas"]["RegistrationResponse"]
export type ResetPasswordRequest = components["schemas"]["ResetPasswordRequest"]
export type TokenResponse = components["schemas"]["TokenResponse"]
export type UserMeResponse = components["schemas"]["UserMeResponse"]
export type ValidationError = components["schemas"]["ValidationError"]
