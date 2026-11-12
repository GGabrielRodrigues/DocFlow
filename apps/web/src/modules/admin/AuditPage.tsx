import { useState } from "react"
import { Icon } from "@/components/Icon"
import { Button, DataTable, EmptyState, PageHeader } from "@/components/ui"
import { formatDateTime } from "@/lib/formatters"
import type { Audit, User } from "@/lib/types"

export type AuditCategory = "Todas as categorias" | "Autenticação" | "Mídia" | "Documento" | "Instituição e Equipe"

export type AuditPeriod = "Todo o período" | "Hoje" | "Últimos 7 dias" | "Últimos 30 dias"

const PAGE_SIZE = 8

function classifyAuditCategory(
  action: string,
): Exclude<AuditCategory, "Todas as categorias"> {
  const lower = action.toLowerCase()
  if (
    lower.includes("acesso") ||
    lower.includes("sessão") ||
    lower.includes("conta")
  ) {
    return "Autenticação"
  }
  if (
    lower.includes("mídia") ||
    lower.includes("processamento") ||
    lower.includes("reprocessamento")
  ) {
    return "Mídia"
  }
  if (lower.includes("documento")) {
    return "Documento"
  }
  return "Instituição e Equipe"
}

function matchesPeriod(dateIso: string, period: AuditPeriod): boolean {
  if (period === "Todo o período") return true
  const diffMs = Date.now() - new Date(dateIso).getTime()
  const dayMs = 86400000
  if (period === "Hoje") return diffMs <= dayMs
  if (period === "Últimos 7 dias") return diffMs <= 7 * dayMs
  return diffMs <= 30 * dayMs
}

export interface AuditPageProps {
  audits: Audit[]
  users: User[]
}

export function AuditPage({ audits, users }: AuditPageProps) {
  const [query, setQuery] = useState("")
  const [userFilter, setUserFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState<AuditCategory>(
    "Todas as categorias",
  )
  const [periodFilter, setPeriodFilter] =
    useState<AuditPeriod>("Todo o período")
  const [page, setPage] = useState(1)

  const filtered = audits.filter((item) => {
    const normalizedQuery = query.trim().toLowerCase()
    const matchesSearch =
      !normalizedQuery ||
      item.action.toLowerCase().includes(normalizedQuery) ||
      item.detail.toLowerCase().includes(normalizedQuery)
    const matchesUser = userFilter === "all" || item.userId === userFilter
    const matchesCategory =
      categoryFilter === "Todas as categorias" ||
      classifyAuditCategory(item.action) === categoryFilter
    const matchesTime = matchesPeriod(item.date, periodFilter)

    return matchesSearch && matchesUser && matchesCategory && matchesTime
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const paginated = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  )

  return (
    <>
      <PageHeader
        eyebrow="AUDITORIA"
        title="Registro de atividades"
        description="Histórico imutável (append-only) e rastreável das ações realizadas nesta instituição (RF-27, RN-11)."
      />
      <section className="panel">
        <div className="toolbar">
          <div className="toolbar__controls">
            <label className="search">
              <Icon name="search" size={17} />
              <input
                aria-label="Buscar eventos de auditoria"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value)
                  setPage(1)
                }}
                placeholder="Buscar por ação ou detalhe..."
              />
            </label>

            <span className="select-wrap">
              <select
                aria-label="Filtrar auditoria por usuário"
                className="input toolbar__select"
                value={userFilter}
                onChange={(event) => {
                  setUserFilter(event.target.value)
                  setPage(1)
                }}
              >
                <option value="all">Todos os usuários</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
              <Icon name="chevron" size={14} />
            </span>

            <span className="select-wrap">
              <select
                aria-label="Filtrar auditoria por categoria"
                className="input toolbar__select"
                value={categoryFilter}
                onChange={(event) => {
                  setCategoryFilter(event.target.value as AuditCategory)
                  setPage(1)
                }}
              >
                <option value="Todas as categorias">Todas as categorias</option>
                <option value="Autenticação">Autenticação</option>
                <option value="Mídia">Mídia</option>
                <option value="Documento">Documento</option>
                <option value="Instituição e Equipe">
                  Instituição e Equipe
                </option>
              </select>
              <Icon name="chevron" size={14} />
            </span>

            <span className="select-wrap">
              <select
                aria-label="Filtrar auditoria por período"
                className="input toolbar__select"
                value={periodFilter}
                onChange={(event) => {
                  setPeriodFilter(event.target.value as AuditPeriod)
                  setPage(1)
                }}
              >
                <option value="Todo o período">Todo o período</option>
                <option value="Hoje">Hoje</option>
                <option value="Últimos 7 dias">Últimos 7 dias</option>
                <option value="Últimos 30 dias">Últimos 30 dias</option>
              </select>
              <Icon name="chevron" size={14} />
            </span>
          </div>
        </div>

        <DataTable
          caption="Histórico de auditoria da instituição"
          headers={["Data e hora", "Usuário", "Categoria", "Ação", "Detalhes"]}
          hasRows={paginated.length > 0}
          emptyState={
            <EmptyState
              title="Nenhuma atividade registrada"
              description="Ajuste os filtros de auditoria ou realize ações na plataforma."
            />
          }
        >
          {paginated.map((item) => (
            <tr key={item.id}>
              <td>{formatDateTime(item.date)}</td>
              <td>
                <strong>
                  {users.find((user) => user.id === item.userId)?.name ||
                    "Usuário"}
                </strong>
              </td>
              <td>{classifyAuditCategory(item.action)}</td>
              <td>{item.action}</td>
              <td>{item.detail}</td>
            </tr>
          ))}
        </DataTable>

        <div className="pagination-bar">
          <span>
            Exibindo <strong>{paginated.length}</strong> de{" "}
            <strong>{filtered.length}</strong> eventos · Trilha imutável (RN-11)
          </span>
          {totalPages > 1 && (
            <div className="pagination-bar__buttons">
              <Button
                variant="secondary"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <span>
                Página {currentPage} de {totalPages}
              </span>
              <Button
                variant="secondary"
                disabled={currentPage >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Próxima
              </Button>
            </div>
          )}
        </div>
      </section>
    </>
  )
}
