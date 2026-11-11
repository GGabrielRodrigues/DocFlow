import { Badge, Button, EmptyState, PageHeader } from "@/components/ui"
import { formatDate, formatDuration, formatFileSize } from "@/lib/formatters"
import type { MediaItem, Page, User } from "@/lib/types"

export function MediaPage({
  media,
  users,
  onNavigate,
}: {
  media: MediaItem[]
  users: User[]
  onNavigate: (page: Page) => void
}) {
  return (
    <>
      <PageHeader
        eyebrow="BIBLIOTECA DE MÍDIAS"
        title="Gravações da instituição"
        description="Acompanhe os vídeos e áudios de reuniões enviados para transcrição."
        action={
          <Button
            variant="secondary"
            icon="mic"
            onClick={() => onNavigate("transcripts")}
          >
            Ver transcrições
          </Button>
        }
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Gravação</th>
                <th>Duração</th>
                <th>Tamanho</th>
                <th>Enviado por</th>
                <th>Data</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {media.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.title}</strong>
                    <br />
                    <small className="muted">{item.fileName}</small>
                  </td>
                  <td>{formatDuration(item.durationSeconds)}</td>
                  <td>{formatFileSize(item.sizeBytes)}</td>
                  <td>
                    {users.find((u) => u.id === item.uploadedBy)?.name ||
                      "Usuário"}
                  </td>
                  <td>{formatDate(item.createdAt)}</td>
                  <td>
                    <Badge status={item.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!media.length && (
          <EmptyState
            icon="video"
            title="Nenhuma mídia enviada"
            description="Envie gravações de reuniões (até 10 GB / 2h30) para gerar transcrições."
          />
        )}
      </section>
    </>
  )
}
