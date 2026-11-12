import { useState } from "react"
import { Icon } from "@/components/Icon"
import { Button, EmptyState, PageHeader } from "@/components/ui"
import { formatDate } from "@/lib/formatters"
import type { Page, TranscriptItem } from "@/lib/types"

export interface TranscriptsPageProps {
  transcripts: TranscriptItem[]
  onNavigate: (page: Page) => void
}

export function TranscriptsPage({
  transcripts,
  onNavigate,
}: TranscriptsPageProps) {
  const [query, setQuery] = useState("")
  const normalizedQuery = query.trim().toLowerCase()

  const visible = transcripts.filter(
    (tr) =>
      !normalizedQuery ||
      tr.title.toLowerCase().includes(normalizedQuery) ||
      tr.segments.some(
        (seg) =>
          seg.text.toLowerCase().includes(normalizedQuery) ||
          seg.speaker.toLowerCase().includes(normalizedQuery),
      ),
  )

  return (
    <>
      <PageHeader
        eyebrow="TRANSCRIÇÕES"
        title="Transcrições com diarização"
        description="Consulte os trechos identificados por falante e utilize-os na geração de atas."
        action={
          <Button icon="plus" onClick={() => onNavigate("create")}>
            Gerar documento
          </Button>
        }
      />

      <section className="panel" style={{ marginBottom: "18px" }}>
        <div className="toolbar" style={{ borderBottom: 0 }}>
          <label className="search" style={{ width: "340px" }}>
            <Icon name="search" size={17} />
            <input
              aria-label="Buscar em transcrições por título, falante ou trecho"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por título, falante ou trecho..."
            />
          </label>
        </div>
      </section>

      {visible.map((transcript) => (
        <section className="panel" key={transcript.id}>
          <div className="panel__header">
            <div>
              <h2>{transcript.title}</h2>
              <p>
                Idioma: {transcript.language} · {transcript.speakersCount}{" "}
                falantes · Atualizado em {formatDate(transcript.updatedAt)}
              </p>
            </div>
          </div>
          <div className="timeline">
            {transcript.segments.map((segment) => (
              <div className="timeline__item" key={segment.id}>
                <span className="timeline__dot" />
                <div>
                  <strong>
                    {segment.speaker} ({segment.startTime} – {segment.endTime})
                  </strong>
                  <p>{segment.text}</p>
                  <small>
                    Confiança: {Math.round(segment.confidence * 100)}%
                  </small>
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
      {!visible.length && (
        <section className="panel">
          <EmptyState
            icon="mic"
            title="Nenhuma transcrição encontrada"
            description="Ajuste a busca ou solicite a transcrição de uma gravação na biblioteca de mídias."
          />
        </section>
      )}
    </>
  )
}
