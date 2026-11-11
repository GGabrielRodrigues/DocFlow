import { Icon } from "@/components/Icon"
import { Button, EmptyState, PageHeader, Stat } from "@/components/ui"
import { firstName, relativeDate } from "@/lib/formatters"
import type { Audit, DocumentItem, Institution, Page, User } from "@/lib/types"
import { DocumentRow } from "@/modules/documents/DocumentsPage"

export function DashboardPage({
  documents,
  users,
  audits,
  allUsers,
  user,
  institution,
  onNavigate,
}: {
  documents: DocumentItem[]
  users: User[]
  audits: Audit[]
  allUsers: User[]
  user: User
  institution: Institution
  onNavigate: (page: Page) => void
}) {
  const pending = documents.filter(
    (doc) => doc.status === "Em validação",
  ).length
  const approved = documents.filter((doc) => doc.status === "Aprovado").length

  return (
    <>
      <PageHeader
        eyebrow="PAINEL DA INSTITUIÇÃO"
        title={`Bom dia, ${firstName(user.name)}.`}
        description={`Acompanhe o que está acontecendo na ${institution.name}.`}
        action={
          <Button icon="plus" onClick={() => onNavigate("create")}>
            Novo documento
          </Button>
        }
      />
      <div className="stats">
        <Stat
          icon="file"
          label="Documentos"
          value={documents.length}
          note="Total da instituição"
        />
        <Stat
          icon="clock"
          label="Em validação"
          value={pending}
          note={pending ? "Aguardando análise" : "Nenhuma pendência"}
          accent="amber"
        />
        <Stat
          icon="check"
          label="Aprovados"
          value={approved}
          note="Documentos concluídos"
          accent="green"
        />
        <Stat
          icon="users"
          label="Pessoas"
          value={users.length}
          note="Contas vinculadas"
          accent="violet"
        />
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <h2>Documentos recentes</h2>
              <p>Últimas movimentações da instituição</p>
            </div>
            <button
              className="text-link"
              onClick={() => onNavigate("documents")}
            >
              Ver todos <Icon name="arrow" size={15} />
            </button>
          </div>
          <div className="document-list">
            {documents.slice(0, 4).map((doc) => (
              <DocumentRow
                key={doc.id}
                doc={doc}
                author={allUsers.find((item) => item.id === doc.authorId)}
              />
            ))}
            {!documents.length && (
              <EmptyState
                title="Nenhum documento criado"
                description="Crie o primeiro documento da sua instituição."
                action={
                  <Button icon="plus" onClick={() => onNavigate("create")}>
                    Criar documento
                  </Button>
                }
              />
            )}
          </div>
        </section>
        <section className="panel">
          <div className="panel__header">
            <div>
              <h2>Atividade recente</h2>
              <p>Ações registradas em auditoria</p>
            </div>
          </div>
          <div className="timeline">
            {audits.slice(0, 5).map((item) => (
              <div className="timeline__item" key={item.id}>
                <span className="timeline__dot" />
                <div>
                  <strong>{item.action}</strong>
                  <p>{item.detail}</p>
                  <small>
                    {allUsers.find((entry) => entry.id === item.userId)?.name ||
                      "Usuário"}{" "}
                    · {relativeDate(item.date)}
                  </small>
                </div>
              </div>
            ))}
            {!audits.length && (
              <p className="empty-line">As atividades aparecerão aqui.</p>
            )}
          </div>
        </section>
      </div>
    </>
  )
}
