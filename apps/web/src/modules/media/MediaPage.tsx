import { FormEvent, useState } from "react"
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
import type { MediaItem, Page, User } from "@/lib/types"

export interface MediaPageProps {
  media: MediaItem[]
  users: User[]
  currentUser: User
  onNavigate: (page: Page) => void
  onUpload?: (mediaItem: MediaItem) => void
}

export function MediaPage({
  media,
  users,
  currentUser,
  onNavigate,
  onUpload,
}: MediaPageProps) {
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [formError, setFormError] = useState("")

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!selectedFile) {
      setFormError("Selecione um arquivo de áudio ou vídeo.")
      return
    }
    const resolvedTitle =
      title.trim() || selectedFile.name.replace(/\.[^/.]+$/, "")

    onUpload?.({
      id: crypto.randomUUID(),
      institutionId: currentUser.institutionId,
      title: resolvedTitle,
      fileName: selectedFile.name,
      durationSeconds: 1800,
      sizeBytes: selectedFile.size || 50 * 1024 * 1024,
      status: "Pronto",
      uploadedBy: currentUser.id,
      createdAt: new Date().toISOString(),
    })

    setTitle("")
    setSelectedFile(null)
    setFormError("")
    setUploadModalOpen(false)
  }

  return (
    <>
      <PageHeader
        eyebrow="BIBLIOTECA DE MÍDIAS"
        title="Gravações da instituição"
        description="Acompanhe os vídeos e áudios de reuniões enviados para transcrição."
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
        <DataTable
          caption="Gravações de áudio e vídeo da instituição"
          headers={[
            "Gravação",
            "Duração",
            "Tamanho",
            "Enviado por",
            "Data",
            "Status",
          ]}
          hasRows={media.length > 0}
          emptyState={
            <EmptyState
              icon="video"
              title="Nenhuma mídia enviada"
              description="Envie gravações de reuniões (até 10 GB / 2h30) para gerar transcrições."
              action={
                <Button icon="upload" onClick={() => setUploadModalOpen(true)}>
                  Enviar gravação
                </Button>
              }
            />
          }
        >
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
                {users.find((u) => u.id === item.uploadedBy)?.name || "Usuário"}
              </td>
              <td>{formatDate(item.createdAt)}</td>
              <td>
                <Badge status={item.status} />
              </td>
            </tr>
          ))}
        </DataTable>
      </section>

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
          <form className="form-stack" onSubmit={handleSubmit}>
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
