import { afterEach, describe, expect, it, vi } from "vitest"
import { docflowTypedApi, openapiRequest } from "@/lib/api-client"
import { setAccessToken } from "@/lib/http-client"

describe("Cliente de API tipado a partir do OpenAPI (FE-03)", () => {
  afterEach(() => {
    setAccessToken(null)
    vi.restoreAllMocks()
  })

  it("realiza chamadas tipadas para endpoints de health e auth definidos em contracts/openapi.json", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ status: "ok", service: "docflow-api" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    )

    const liveness = await docflowTypedApi.health.checkLiveness()
    expect(liveness.status).toBe("ok")
    expect(liveness.service).toBe("docflow-api")

    const [calledUrl, calledInit] = fetchMock.mock.calls[0]
    expect(String(calledUrl)).toContain("/health")
    expect(calledInit?.method).toBe("GET")
  })

  it("serializa parâmetros de rota e query tipados para endpoints de auditoria (/api/v1/audit)", async () => {
    setAccessToken("jwt-openapi-test")
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [],
            total: 0,
            page: 2,
            page_size: 10,
            total_pages: 0,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "log-123",
            institution_id: "inst-1",
            action: "user.login",
            resource_type: "session",
            created_at: "2026-11-11T12:00:00Z",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      )

    const pageResult = await docflowTypedApi.audit.listAuditLogs({
      action: "user.login",
      page: 2,
      page_size: 10,
    })

    expect(pageResult.page).toBe(2)
    const [listUrl, listInit] = fetchMock.mock.calls[0]
    expect(String(listUrl)).toContain("/api/v1/audit")
    expect(String(listUrl)).toContain("action=user.login")
    expect(String(listUrl)).toContain("page=2")
    expect(String(listUrl)).toContain("page_size=10")
    const headers = new Headers(listInit?.headers)
    expect(headers.get("Authorization")).toBe("Bearer jwt-openapi-test")

    const itemResult = await openapiRequest("/api/v1/audit/{log_id}", "get", {
      pathParams: { log_id: "log-123" },
    })
    expect(itemResult.id).toBe("log-123")
    const [detailUrl] = fetchMock.mock.calls[1]
    expect(String(detailUrl)).toContain("/api/v1/audit/log-123")
  })
})
