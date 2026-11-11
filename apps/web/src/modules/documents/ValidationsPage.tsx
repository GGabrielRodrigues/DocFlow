import { Icon } from "@/components/Icon"
import { Badge, Button, EmptyState, PageHeader } from "@/components/ui"
import { formatDate } from "@/lib/formatters"
import type { DocumentItem, DocumentStatus, User } from "@/lib/types"

export function ValidationsPage({
  documents,
  users,
  isAdmin,
  update,
}: {
  documents: DocumentItem[]
  users: User[]
  isAdmin: boolean
  update: (id: string, status: DocumentStatus) => void
}) {
  const pending = documents.filter((doc) => doc.status === "Em validação")

  return (
    <>
      <PageHeader
        eyebrow="VALIDAÇÕES"
        title="Fila de validação"
        description={
          isAdmin
            ? "Analise os documentos encaminhados pela equipe."
            : "Acompanhe os documentos enviados para análise."
        }
      />
      <section className="panel validation-list">
        {pending.map((doc) => (
          <div className="validation-row" key={doc.id}>
            <span className="document-row__icon">
              <Icon name="file" />
            </span>
            <div>
              <strong>{doc.title}</strong>
              <p>{doc.content}</p>
              <small>
                Enviado por{" "}
                {users.find((item) => item.id === doc.authorId)?.name} ·{" "}
                {formatDate(doc.updatedAt)}
              </small>
            </div>
            <Badge status={doc.status} />
            {isAdmin && (
              <div className="validation-row__actions">
                <Button
                  variant="secondary"
                  onClick={() => update(doc.id, "Devolvido")}
                >
                  Devolver
                </Button>
                <Button onClick={() => update(doc.id, "Aprovado")}>
                  Aprovar
                </Button>
              </div>
            )}
          </div>
        ))}
        {!pending.length && (
          <EmptyState
            icon="check"
            title="Tudo em dia"
            description="Não há documentos aguardando validação."
          />
        )}
      </section>
    </>
  )
}
