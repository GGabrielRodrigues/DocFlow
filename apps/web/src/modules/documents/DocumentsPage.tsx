import { useState } from "react"
import { Icon } from "@/components/Icon"
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui"
import { formatDate } from "@/lib/formatters"
import type { DocumentItem, Page, User } from "@/lib/types"

export function DocumentsPage({
  documents,
  users,
  onNavigate,
}: {
  documents: DocumentItem[]
  users: User[]
  onNavigate: (page: Page) => void
}) {
  const [query, setQuery] = useState("")
  const [filter, setFilter] = useState("Todos")

  const visible = documents.filter(
    (doc) =>
      (filter === "Todos" || doc.status === filter) &&
      doc.title.toLowerCase().includes(query.toLowerCase()),
  )

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
          <label className="search">
            <Icon name="search" size={17} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por título..."
            />
          </label>
          <div className="filter-tabs">
            {["Todos", "Rascunho", "Em validação", "Aprovado", "Devolvido"].map(
              (item) => (
                <button
                  className={filter === item ? "active" : ""}
                  onClick={() => setFilter(item)}
                  key={item}
                >
                  {item}
                </button>
              ),
            )}
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Documento</th>
                <th>Tipo</th>
                <th>Responsável</th>
                <th>Atualizado</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
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
            </tbody>
          </table>
        </div>
        {!visible.length && (
          <EmptyState
            title="Nenhum documento encontrado"
            description="Ajuste os filtros ou crie um novo documento."
          />
        )}
      </section>
    </>
  )
}

export function DocumentRow({
  doc,
  author,
}: {
  doc: DocumentItem
  author?: User
}) {
  return (
    <div className="document-row">
      <span className="document-row__icon">
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
