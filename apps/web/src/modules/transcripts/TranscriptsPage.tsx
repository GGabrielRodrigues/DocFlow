import { Button, EmptyState, PageHeader } from "@/components/ui"
import { formatDate } from "@/lib/formatters"
import type { Page, TranscriptItem } from "@/lib/types"

export function TranscriptsPage({
  transcripts,
  onNavigate,
}: {
  transcripts: TranscriptItem[]
  onNavigate: (page: Page) => void
}) {
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
      {transcripts.map((transcript) => (
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
      {!transcripts.length && (
        <section className="panel">
          <EmptyState
            icon="mic"
            title="Nenhuma transcrição disponível"
            description="Solicite a transcrição de uma gravação na biblioteca de mídias."
          />
        </section>
      )}
    </>
  )
}
