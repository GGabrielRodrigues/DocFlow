import { afterEach, describe, expect, it, vi } from "vitest"
import { createPublicEnv } from "@/lib/env"
import {
  ApiProblemError,
  getAccessToken,
  httpClient,
  onGlobalApiError,
  setAccessToken,
} from "@/lib/http-client"

describe("env & httpClient (FE-01)", () => {
  afterEach(() => {
    setAccessToken(null)
    vi.restoreAllMocks()
  })

  it("normaliza VITE_API_BASE_URL removendo barra final e aplica fallback padrão", () => {
    const customEnv = createPublicEnv({
      VITE_API_BASE_URL: "https://docflow-api.gabrieldevops.dev.br/api/v1/",
      VITE_APP_ENV: "production",
    })
    expect(customEnv.apiBaseUrl).toBe(
      "https://docflow-api.gabrieldevops.dev.br/api/v1",
    )
    expect(customEnv.appEnv).toBe("production")

    const fallbackEnv = createPublicEnv({})
    expect(fallbackEnv.apiBaseUrl).toBe("http://localhost:8000/api/v1")
    expect(fallbackEnv.appEnv).toBe("development")
  })

  it("envia X-Request-ID e Authorization Bearer token em memória nas requisições", async () => {
    setAccessToken("jwt-token-123")
    expect(getAccessToken()).toBe("jwt-token-123")

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    )

    const result = await httpClient.get<{ status: string }>("/health")
    expect(result).toEqual({ status: "ok" })
    expect(fetchSpy).toHaveBeenCalledTimes(1)

    const [, requestInit] = fetchSpy.mock.calls[0]!
    const headers = new Headers(requestInit?.headers)
    expect(headers.get("Authorization")).toBe("Bearer jwt-token-123")
    expect(headers.get("X-Request-ID")).toBeTruthy()
  })

  it("converte respostas de erro no formato RFC 9457 (Problem Details) e notifica o handler global", async () => {
    const capturedErrors: ApiProblemError[] = []
    const unsubscribe = onGlobalApiError((err) => capturedErrors.push(err))

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          type: "https://api.docflow.com.br/errors/mandatory-fields-pending",
          title: "Campos obrigatórios pendentes",
          status: 422,
          detail: "Existem 2 campos obrigatórios pendentes.",
          request_id: "req_123",
          errors: [
            {
              field: "data_reuniao",
              code: "field_pending",
              message: "Data da reunião está pendente.",
            },
          ],
        }),
        {
          status: 422,
          headers: { "content-type": "application/problem+json" },
        },
      ),
    )

    await expect(
      httpClient.post("/documents/1/approve"),
    ).rejects.toBeInstanceOf(ApiProblemError)

    expect(capturedErrors).toHaveLength(1)
    expect(capturedErrors[0]?.status).toBe(422)
    expect(capturedErrors[0]?.requestId).toBe("req_123")
    expect(capturedErrors[0]?.errors[0]?.field).toBe("data_reuniao")

    unsubscribe()
  })
})
