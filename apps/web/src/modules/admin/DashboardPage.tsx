import { Icon } from "@/components/Icon"
import { Badge, Button, EmptyState, PageHeader, Stat } from "@/components/ui"
import { firstName, formatDuration, relativeDate } from "@/lib/formatters"
import type {
  Audit,
  DocumentItem,
  Institution,
  MediaItem,
  Page,
  User,
} from "@/lib/types"
import { DocumentRow } from "@/modules/documents/DocumentsPage"

export interface DashboardPageProps {
  documents: DocumentItem[]
  media?: MediaItem[]
  users: User[]
  audits: Audit[]
  allUsers: User[]
  user: User
  institution: Institution
  onNavigate: (page: Page) => void
}

export function DashboardPage({
  documents,
  media = [],
  users,
  audits,
  allUsers,
  user,
  institution,
  onNavigate,
}: DashboardPageProps) {
  const drafts = documents.filter((doc) => doc.status === "Rascunho").length
  const pending = documents.filter(
    (doc) => doc.status === "Em validação",
  ).length
  const approved = documents.filter((doc) => doc.status === "Aprovado").length
  const returned = documents.filter((doc) => doc.status === "Devolvido").length

  const processingMedia = media.filter(
    (item) => item.status === "Na fila" || item.status === "Em processamento",
  )

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
          icon="video"
          label="Mídias em fila"
          value={processingMedia.length}
          note={`${media.length} gravações no total`}
          accent="violet"
        />
        <Stat
          icon="check"
          label="Aprovados"
          value={approved}
          note={`${users.length} pessoas na equipe`}
          accent="green"
        />
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <h2>Documentos por status e recentes</h2>
              <p>Distribuição atual e últimas movimentações da instituição</p>
            </div>
            <button
              type="button"
              className="text-link"
              onClick={() => onNavigate("documents")}
            >
              Ver todos <Icon name="arrow" size={15} />
            </button>
          </div>

          <div
            className="status-breakdown"
            role="group"
            aria-label="Documentos por status"
          >
            <div className="status-pill">
              <strong>{String(drafts).padStart(2, "0")}</strong>
              <span>Rascunho</span>
            </div>
            <div className="status-pill">
              <strong>{String(pending).padStart(2, "0")}</strong>
              <span>Em validação</span>
            </div>
            <div className="status-pill">
              <strong>{String(approved).padStart(2, "0")}</strong>
              <span>Aprovado</span>
            </div>
            <div className="status-pill">
              <strong>{String(returned).padStart(2, "0")}</strong>
              <span>Devolvido</span>
            </div>
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

        <div className="form-stack">
          <section className="panel">
            <div className="panel__header">
              <div>
                <h2>Mídias em processamento</h2>
                <p>Fila assíncrona de gravações e transcrições</p>
              </div>
              <button
                type="button"
                className="text-link"
                onClick={() => onNavigate("media")}
              >
                Biblioteca <Icon name="arrow" size={15} />
              </button>
            </div>
            <div className="document-list">
              {(processingMedia.length > 0
                ? processingMedia
                : media.slice(0, 2)
              ).map((item) => (
                <div className="document-row" key={item.id}>
                  <span className="document-row__icon" aria-hidden="true">
                    <Icon name="video" />
                  </span>
                  <span className="document-row__main">
                    <strong>{item.title}</strong>
                    <small>
                      {item.fileName} · {formatDuration(item.durationSeconds)}
                    </small>
                  </span>
                  <Badge status={item.status} />
                </div>
              ))}
              {!media.length && (
                <p className="empty-line">Nenhuma gravação enviada.</p>
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
                      {allUsers.find((entry) => entry.id === item.userId)
                        ?.name || "Usuário"}{" "}
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
      </div>
    </>
  )
}
