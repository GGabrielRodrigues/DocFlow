import { useState } from "react"
import { Icon } from "@/components/Icon"
import {
  Badge,
  Button,
  DataTable,
  EmptyState,
  PageHeader,
} from "@/components/ui"
import { formatDate } from "@/lib/formatters"
import type { DocumentItem, Page, User } from "@/lib/types"

export interface DocumentsPageProps {
  documents: DocumentItem[]
  users: User[]
  onNavigate: (page: Page) => void
}

export function DocumentsPage({
  documents,
  users,
  onNavigate,
}: DocumentsPageProps) {
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState("Todos")
  const [typeFilter, setTypeFilter] = useState("Todos os tipos")

  const visible = documents.filter((doc) => {
    const matchesStatus = filter === "Todos" || doc.status === filter
    const matchesType =
      typeFilter === "Todos os tipos" || doc.type === typeFilter
    const normalizedQuery = query.trim().toLowerCase()
    const matchesQuery =
      !normalizedQuery ||
      doc.title.toLowerCase().includes(normalizedQuery) ||
      doc.content.toLowerCase().includes(normalizedQuery)
    return matchesStatus && matchesType && matchesQuery
  })

  return (
    <>
      <PageHeader
        eyebrow="DOCUMENTOS"
        title="Documentos da instituição"
        description="Crie, acompanhe e consulte todos os documentos administrativos."
        action={
          <Button icon="plus" onClick={() => onNavigate("create")}>
            Novo documento
          </Button>
        }
      />
      <section className="panel">
        <div className="toolbar">
          <div className="toolbar__controls">
            <label className="search">
              <Icon name="search" size={17} />
              <input
                aria-label="Buscar documentos por título"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar por título..."
              />
            </label>
            <span className="select-wrap">
              <select
                aria-label="Filtrar documentos por tipo"
                className="input toolbar__select"
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
              >
                <option value="Todos os tipos">Todos os tipos</option>
                <option value="Ata">Ata</option>
                <option value="Ofício">Ofício</option>
                <option value="Prestação de contas">Prestação de contas</option>
              </select>
              <Icon name="chevron" size={14} />
            </span>
          </div>
          <div
            className="filter-tabs"
            role="group"
            aria-label="Filtrar documentos por status"
          >
            {["Todos", "Rascunho", "Em validação", "Aprovado", "Devolvido"].map(
              (item) => (
                <button
                  type="button"
                  className={filter === item ? "active" : ""}
                  aria-pressed={filter === item}
                  onClick={() => setFilter(item)}
                  key={item}
                >
                  {item}
                </button>
              ),
            )}
          </div>
        </div>
        <DataTable
          caption="Lista de documentos administrativos da instituição"
          headers={["Documento", "Tipo", "Responsável", "Atualizado", "Status"]}
          hasRows={visible.length > 0}
          emptyState={
            <EmptyState
              title="Nenhum documento encontrado"
              description="Ajuste os filtros ou crie um novo documento."
            />
          }
        >
          {visible.map((doc) => (
            <tr key={doc.id}>
              <td>
                <strong>{doc.title}</strong>
              </td>
              <td>{doc.type}</td>
              <td>
                {users.find((item) => item.id === doc.authorId)?.name ||
                  "Usuário"}
              </td>
              <td>{formatDate(doc.updatedAt)}</td>
              <td>
                <Badge status={doc.status} />
              </td>
            </tr>
          ))}
        </DataTable>
      </section>
    </>
  )
}

export interface DocumentRowProps {
  doc: DocumentItem
  author?: User
}

export function DocumentRow({ doc, author }: DocumentRowProps) {
  return (
    <div className="document-row">
      <span className="document-row__icon" aria-hidden="true">
        <Icon name="file" />
      </span>
      <span className="document-row__main">
        <strong>{doc.title}</strong>
        <small>
          {doc.type} · {author?.name || "Usuário"}
        </small>
      </span>
      <span className="document-row__date">{formatDate(doc.updatedAt)}</span>
      <Badge status={doc.status} />
    </div>
  )
}
