import { FormEvent, useState } from "react"
import { Icon } from "@/components/Icon"
import {
  Badge,
  Button,
  DataTable,
  EmptyState,
  Field,
  FileUpload,
  Modal,
  PageHeader,
} from "@/components/ui"
import { formatDate, formatDuration, formatFileSize } from "@/lib/formatters"
import { docflowApi, inferMediaKind } from "@/lib/mock-api"
import type { MediaItem, MediaKind, MediaStatus, Page, User } from "@/lib/types"
import { useMediaRealtime } from "./media-realtime"

const STATUS_FILTERS: ("Todos" | MediaStatus)[] = [
  "Todos",
  "Na fila",
  "Em processamento",
  "Pronto",
  "Transcrito",
  "Falhou",
  "Cancelado",
]

export interface MediaPageProps {
  media: MediaItem[]
  users: User[]
  currentUser: User
  pollIntervalMs?: number
  onNavigate: (page: Page) => void
  onUpload?: (mediaItem: MediaItem) => void
  onDelete?: (mediaId: string) => void
  onCancelJob?: (mediaId: string) => void
  onRetryJob?: (mediaId: string) => void
  onDownload?: (mediaItem: MediaItem, signedUrl: string) => void
  onRefresh?: () => void
  onNotify?: (message: string) => void
}

export function MediaPage({
  media,
  users,
  currentUser,
  pollIntervalMs = 2500,
  onNavigate,
  onUpload,
  onDelete,
  onCancelJob,
  onRetryJob,
  onDownload,
  onRefresh,
  onNotify,
}: MediaPageProps) {
  const [query, setQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<"Todos" | MediaStatus>(
    "Todos",
  )
  const [kindFilter, setKindFilter] = useState<"Todos os formatos" | MediaKind>(
    "Todos os formatos",
  )

  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [previewMedia, setPreviewMedia] = useState<MediaItem | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<MediaItem | null>(null)

  const [title, setTitle] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [formError, setFormError] = useState("")

  const isAdmin = currentUser.role === "Administrador da instituição"

  const { hasActiveJobs } = useMediaRealtime({
    media,
    institutionId: currentUser.institutionId,
    pollIntervalMs,
    onRefresh: () => onRefresh?.(),
    onCompleted: (completedTitles) => {
      if (completedTitles.length === 1) {
        onNotify?.(`Processamento concluído: "${completedTitles[0]}".`)
      } else if (completedTitles.length > 1) {
        onNotify?.(
          `${completedTitles.length} gravações concluíram o processamento.`,
        )
      }
    },
  })

  const visible = media.filter((item) => {
    const resolvedKind =
      item.kind || inferMediaKind(item.fileName, item.mimeType)
    const matchesStatus =
      statusFilter === "Todos" || item.status === statusFilter
    const matchesKind =
      kindFilter === "Todos os formatos" || resolvedKind === kindFilter
    const normalizedQuery = query.trim().toLowerCase()
    const matchesQuery =
      !normalizedQuery ||
      item.title.toLowerCase().includes(normalizedQuery) ||
      item.fileName.toLowerCase().includes(normalizedQuery)
    return matchesStatus && matchesKind && matchesQuery
  })

  const canManageMedia = (item: MediaItem): boolean => {
    return isAdmin || item.uploadedBy === currentUser.id
  }

  const handleUploadSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!selectedFile) {
      setFormError("Selecione um arquivo de áudio ou vídeo.")
      return
    }
    const resolvedTitle =
      title.trim() || selectedFile.name.replace(/\.[^/.]+$/, "")
    const kind = inferMediaKind(selectedFile.name, selectedFile.type)

    onUpload?.({
      id: crypto.randomUUID(),
      institutionId: currentUser.institutionId,
      title: resolvedTitle,
      fileName: selectedFile.name,
      kind,
      mimeType:
        selectedFile.type || (kind === "Áudio" ? "audio/mpeg" : "video/mp4"),
      durationSeconds: 1800,
      sizeBytes: selectedFile.size || 50 * 1024 * 1024,
      status: "Na fila",
      progressPercent: 15,
      uploadedBy: currentUser.id,
      createdAt: new Date().toISOString(),
    })

    setTitle("")
    setSelectedFile(null)
    setFormError("")
    setUploadModalOpen(false)
  }

  const handleDownload = (item: MediaItem) => {
    const signedUrl = docflowApi.getSignedMediaUrl(
      currentUser,
      item.id,
      "download",
    )
    onDownload?.(item, signedUrl)
    onNotify?.(`Download iniciado: "${item.fileName}".`)
  }

  return (
    <>
      <PageHeader
        eyebrow="BIBLIOTECA DE MÍDIAS"
        title="Gravações da instituição"
        description="Gerencie vídeos e áudios de reuniões, acompanhe o processamento em tempo real e pré-visualize gravações."
        action={
          <div className="form-actions">
            <Button
              variant="secondary"
              icon="mic"
              onClick={() => onNavigate("transcripts")}
            >
              Ver transcrições
            </Button>
            <Button icon="upload" onClick={() => setUploadModalOpen(true)}>
              Enviar gravação
            </Button>
          </div>
        }
      />

      <section className="panel">
        {hasActiveJobs && (
          <div
            className="realtime-banner"
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <span className="realtime-banner__pulse">
              <span className="realtime-banner__dot" aria-hidden="true" />
              Sincronizando status de processamento em tempo real
              (SSE/Polling)...
            </span>
            <small>Atualização automática ativa</small>
          </div>
        )}

        <div className="toolbar">
          <div className="toolbar__controls">
            <label className="search">
              <Icon name="search" size={17} />
              <input
                aria-label="Buscar mídias por título ou arquivo"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar por título ou arquivo..."
              />
            </label>
            <span className="select-wrap">
              <select
                aria-label="Filtrar por formato de mídia"
                className="input toolbar__select"
                value={kindFilter}
                onChange={(event) =>
                  setKindFilter(
                    event.target.value as "Todos os formatos" | MediaKind,
                  )
                }
              >
                <option value="Todos os formatos">Todos os formatos</option>
                <option value="Vídeo">Vídeo</option>
                <option value="Áudio">Áudio</option>
              </select>
              <Icon name="chevron" size={14} />
            </span>
          </div>

          <div
            className="filter-tabs"
            role="group"
            aria-label="Filtrar mídias por status"
          >
            {STATUS_FILTERS.map((item) => (
              <button
                type="button"
                className={statusFilter === item ? "active" : ""}
                aria-pressed={statusFilter === item}
                onClick={() => setStatusFilter(item)}
                key={item}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <DataTable
          caption="Gravações de áudio e vídeo da instituição"
          headers={[
            "Gravação",
            "Formato",
            "Duração",
            "Tamanho",
            "Enviado por",
            "Data",
            "Status",
            "Ações",
          ]}
          hasRows={visible.length > 0}
          emptyState={
            <EmptyState
              icon="video"
              title="Nenhuma mídia encontrada"
              description="Ajuste os filtros de busca ou envie uma nova gravação de reunião (até 10 GB / 2h30)."
              action={
                <Button icon="upload" onClick={() => setUploadModalOpen(true)}>
                  Enviar gravação
                </Button>
              }
            />
          }
        >
          {visible.map((item) => {
            const resolvedKind =
              item.kind || inferMediaKind(item.fileName, item.mimeType)
            const isProcessing =
              item.status === "Na fila" || item.status === "Em processamento"
            const isFailedOrCanceled =
              item.status === "Falhou" || item.status === "Cancelado"
            const progressValue =
              item.progressPercent ?? (isProcessing ? 25 : 100)

            return (
              <tr key={item.id}>
                <td>
                  <strong>{item.title}</strong>
                  <br />
                  <small className="muted">{item.fileName}</small>
                </td>
                <td>{resolvedKind}</td>
                <td>{formatDuration(item.durationSeconds)}</td>
                <td>{formatFileSize(item.sizeBytes)}</td>
                <td>
                  {users.find((u) => u.id === item.uploadedBy)?.name ||
                    "Usuário"}
                </td>
                <td>{formatDate(item.createdAt)}</td>
                <td>
                  <div className="media-status-cell">
                    <Badge status={item.status} />
                    {isProcessing && (
                      <>
                        <div
                          className="upload-progress"
                          role="progressbar"
                          aria-label={`Progresso de ${item.title}`}
                          aria-valuenow={progressValue}
                          aria-valuemin={0}
                          aria-valuemax={100}
                        >
                          <div
                            className="upload-progress__bar"
                            style={{ width: `${progressValue}%` }}
                          />
                        </div>
                        <small>{progressValue}% concluído</small>
                      </>
                    )}
                    {item.errorMessage && (
                      <small className="field__error">
                        {item.errorMessage}
                      </small>
                    )}
                  </div>
                </td>
                <td>
                  <div className="media-actions">
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => setPreviewMedia(item)}
                      aria-label={`Pré-visualizar ${item.title}`}
                      title="Pré-visualizar"
                    >
                      <Icon name="play" size={16} />
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => handleDownload(item)}
                      aria-label={`Baixar ${item.title}`}
                      title="Baixar arquivo"
                    >
                      <Icon name="download" size={16} />
                    </button>
                    {isProcessing && canManageMedia(item) && (
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => onCancelJob?.(item.id)}
                        aria-label={`Cancelar processamento de ${item.title}`}
                        title="Cancelar processamento"
                      >
                        <Icon name="close" size={16} />
                      </button>
                    )}
                    {isFailedOrCanceled && canManageMedia(item) && (
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => onRetryJob?.(item.id)}
                        aria-label={`Reprocessar ${item.title}`}
                        title="Reprocessar"
                      >
                        <Icon name="refresh" size={16} />
                      </button>
                    )}
                    {canManageMedia(item) && (
                      <button
                        type="button"
                        className="icon-button icon-button--danger"
                        onClick={() => setDeleteTarget(item)}
                        aria-label={`Excluir ${item.title}`}
                        title="Excluir mídia"
                      >
                        <Icon name="trash" size={16} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </DataTable>
      </section>

      {previewMedia && (
        <Modal
          eyebrow="PRÉ-VISUALIZAÇÃO DE MÍDIA"
          title={previewMedia.title}
          description={`Arquivo: ${previewMedia.fileName} · URL temporária assinada (Silo/S3)`}
          onClose={() => setPreviewMedia(null)}
        >
          <div className="media-preview">
            {(previewMedia.kind ||
              inferMediaKind(previewMedia.fileName, previewMedia.mimeType)) ===
            "Áudio" ? (
              <audio
                controls
                className="media-preview__audio"
                aria-label={`Player de áudio de ${previewMedia.title}`}
                src={docflowApi.getSignedMediaUrl(
                  currentUser,
                  previewMedia.id,
                  "preview",
                )}
              >
                Seu navegador não suporta reprodução de áudio.
              </audio>
            ) : (
              <video
                controls
                className="media-preview__player"
                aria-label={`Player de vídeo de ${previewMedia.title}`}
                src={docflowApi.getSignedMediaUrl(
                  currentUser,
                  previewMedia.id,
                  "preview",
                )}
              >
                Seu navegador não suporta reprodução de vídeo.
              </video>
            )}

            <dl className="details-grid">
              <div>
                <dt>Formato</dt>
                <dd>
                  {previewMedia.kind ||
                    inferMediaKind(
                      previewMedia.fileName,
                      previewMedia.mimeType,
                    )}
                </dd>
              </div>
              <div>
                <dt>Duração</dt>
                <dd>{formatDuration(previewMedia.durationSeconds)}</dd>
              </div>
              <div>
                <dt>Tamanho</dt>
                <dd>{formatFileSize(previewMedia.sizeBytes)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <Badge status={previewMedia.status} />
                </dd>
              </div>
            </dl>

            <div className="form-actions">
              <Button variant="secondary" onClick={() => setPreviewMedia(null)}>
                Fechar
              </Button>
              <Button
                icon="download"
                onClick={() => handleDownload(previewMedia)}
              >
                Baixar original
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <Modal
          eyebrow="CONFIRMAR EXCLUSÃO"
          title={`Excluir "${deleteTarget.title}"?`}
          description="Esta ação removerá permanentemente o arquivo original do armazenamento S3 (Silo) e as transcrições derivadas. Documentos já aprovados permanecem preservados (RN-14)."
          onClose={() => setDeleteTarget(null)}
        >
          <div className="form-actions">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              icon="trash"
              onClick={() => {
                onDelete?.(deleteTarget.id)
                setDeleteTarget(null)
              }}
            >
              Confirmar exclusão
            </Button>
          </div>
        </Modal>
      )}

      {uploadModalOpen && (
        <Modal
          eyebrow="UPLOAD DE MÍDIA"
          title="Enviar gravação de reunião"
          description="Envie vídeos ou áudios em português (pt-BR) com até 10 GB e duração máxima de 2h30."
          onClose={() => {
            setUploadModalOpen(false)
            setFormError("")
          }}
        >
          <form className="form-stack" onSubmit={handleUploadSubmit}>
            {formError && (
              <div className="form-alert" role="alert">
                {formError}
              </div>
            )}
            <Field
              label="Título da reunião"
              optional
              placeholder="Ex.: Reunião do Conselho Escolar — Junho"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <FileUpload
              onFileSelect={(file) => {
                setSelectedFile(file)
                setFormError("")
              }}
            />
            <div className="form-actions">
              <Button
                variant="secondary"
                onClick={() => setUploadModalOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" icon="upload">
                Confirmar envio
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
