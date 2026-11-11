import { Icon } from "@/components/Icon"
import { Button, PageHeader } from "@/components/ui"
import type { Template } from "@/lib/types"

export function TemplatesPage({
  templates,
  onUse,
}: {
  templates: Template[]
  onUse: () => void
}) {
  return (
    <>
      <PageHeader
        eyebrow="MODELOS"
        title="Modelos de documentos"
        description="Estruturas disponíveis para padronizar a criação de documentos."
      />
      <div className="card-grid">
        {templates.map((template) => (
          <article className="template-card" key={template.id}>
            <span className="template-card__icon">
              <Icon name="layers" />
            </span>
            <span className="eyebrow">{template.type}</span>
            <h3>{template.name}</h3>
            <p>{template.description}</p>
            <Button variant="secondary" onClick={onUse}>
              Usar modelo
            </Button>
          </article>
        ))}
      </div>
    </>
  )
}
