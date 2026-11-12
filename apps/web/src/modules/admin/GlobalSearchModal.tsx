import { useState } from "react"
import { Icon } from "@/components/Icon"
import { Badge, EmptyState, Modal } from "@/components/ui"
import type { DocumentItem, MediaItem, Page, TranscriptItem } from "@/lib/types"

export type GlobalSearchScope = "Tudo" | "Documentos" | "Mídias" | "Transcrições"

export interface GlobalSearchModalProps {
  documents: DocumentItem[]
  media: MediaItem[]
  transcripts: TranscriptItem[]
  onNavigate: (page: Page) => void
  onClose: () => void
}

export function GlobalSearchModal({
  documents,
  media,
  transcripts,
  onNavigate,
  onClose,
}: GlobalSearchModalProps) {
  const [query, setQuery] = useState("")
  const [scope, setScope] = useState<GlobalSearchScope>("Tudo")

  const normalizedQuery = query.trim().toLowerCase()

  const matchedDocuments =
    scope === "Tudo" || scope === "Documentos"
      ? documents.filter(
          (doc) =>
            !normalizedQuery ||
            doc.title.toLowerCase().includes(normalizedQuery) ||
            doc.type.toLowerCase().includes(normalizedQuery) ||
            doc.content.toLowerCase().includes(normalizedQuery),
        )
      : []

  const matchedMedia =
    scope === "Tudo" || scope === "Mídias"
      ? media.filter(
          (item) =>
            !normalizedQuery ||
            item.title.toLowerCase().includes(normalizedQuery) ||
            item.fileName.toLowerCase().includes(normalizedQuery),
        )
      : []

  const matchedTranscripts =
    scope === "Tudo" || scope === "Transcrições"
      ? transcripts.filter(
          (tr) =>
            !normalizedQuery ||
            tr.title.toLowerCase().includes(normalizedQuery) ||
            tr.segments.some(
              (seg) =>
                seg.text.toLowerCase().includes(normalizedQuery) ||
                seg.speaker.toLowerCase().includes(normalizedQuery),
            ),
        )
      : []

  const totalResults =
    matchedDocuments.length + matchedMedia.length + matchedTranscripts.length

  const handleSelectPage = (page: Page) => {
    onNavigate(page)
    onClose()
  }

  return (
    <Modal
      eyebrow="BUSCA GLOBAL (RF-29)"
      title="Pesquisar na instituição"
      description="Busque rapidamente em documentos, gravações de mídia e trechos de transcrições."
      onClose={onClose}
    >
      <div className="form-stack">
        <label className="search" style={{ width: "100%" }}>
          <Icon name="search" size={17} />
          <input
            aria-label="Termo de busca global"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Digite título, assunto, arquivo, falante ou trecho..."
          />
        </label>

        <div
          className="filter-tabs"
          role="group"
          aria-label="Filtrar resultados da busca global"
        >
          {([
            "Tudo",
            "Documentos",
            "Mídias",
            "Transcrições",
          ] as GlobalSearchScope[]).map((item) => (
            <button
              type="button"
              key={item}
              className={scope === item ? "active" : ""}
              aria-pressed={scope === item}
              onClick={() => setScope(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div
          className="global-search-results"
          role="region"
          aria-label="Resultados da busca global"
        >
          {matchedDocuments.map((doc) => (
            <button
              type="button"
              key={`doc-${doc.id}`}
              className="global-search-item"
              onClick={() => handleSelectPage("documents")}
            >
              <span className="document-row__icon" aria-hidden="true">
                <Icon name="file" />
              </span>
              <div>
                <strong>{doc.title}</strong>
                <small>Documento · {doc.type}</small>
              </div>
              <Badge status={doc.status} />
            </button>
          ))}

          {matchedMedia.map((item) => (
            <button
              type="button"
              key={`media-${item.id}`}
              className="global-search-item"
              onClick={() => handleSelectPage("media")}
            >
              <span className="document-row__icon" aria-hidden="true">
                <Icon name="video" />
              </span>
              <div>
                <strong>{item.title}</strong>
                <small>Mídia · {item.fileName}</small>
              </div>
              <Badge status={item.status} />
            </button>
          ))}

          {matchedTranscripts.map((tr) => (
            <button
              type="button"
              key={`tr-${tr.id}`}
              className="global-search-item"
              onClick={() => handleSelectPage("transcripts")}
            >
              <span className="document-row__icon" aria-hidden="true">
                <Icon name="mic" />
              </span>
              <div>
                <strong>{tr.title}</strong>
                <small>
                  Transcrição · {tr.speakersCount} falantes ·{" "}
                  {tr.segments.length} trechos
                </small>
              </div>
              <Icon name="arrow" size={16} />
            </button>
          ))}

          {totalResults === 0 && (
            <EmptyState
              icon="search"
              title="Nenhum resultado encontrado"
              description="Tente outros termos ou altere a categoria selecionada."
            />
          )}
        </div>
      </div>
    </Modal>
  )
}
