import { useState } from "react"
import { Icon } from "@/components/Icon"
import {
  Button,
  Field,
  PageHeader,
  SelectField,
  TextArea,
} from "@/components/ui"
import type { DocumentItem, DocumentStatus, Template, User } from "@/lib/types"

export function DocumentFormPage({
  templates,
  user,
  save,
}: {
  templates: Template[]
  user: User
  save: (doc: DocumentItem) => void
}) {
  const [form, setForm] = useState({
    title: "",
    type: "Ata" as DocumentItem["type"],
    templateId: templates[0]?.id || "",
    content: "",
  })
  const [error, setError] = useState("")

  const submit = (status: DocumentStatus) => {
    if (!form.title.trim() || !form.content.trim()) {
      setError("Preencha o título e as informações do documento.")
      return
    }
    save({
      id: crypto.randomUUID(),
      institutionId: user.institutionId,
      title: form.title.trim(),
      type: form.type,
      content: form.content.trim(),
      status,
      authorId: user.id,
      updatedAt: new Date().toISOString(),
    })
  }

  return (
    <>
      <PageHeader
        eyebrow="NOVO DOCUMENTO"
        title="Criar documento"
        description="Preencha as informações para gerar um novo documento administrativo."
      />
      <div className="editor-grid">
        <section className="panel form-panel">
          {error && <div className="form-alert">{error}</div>}
          <Field
            label="Título do documento"
            placeholder="Ex.: Ata da reunião pedagógica — Junho"
            value={form.title}
            onChange={(event) => {
              setForm({ ...form, title: event.target.value })
              setError("")
            }}
          />
          <div className="form-grid">
            <SelectField
              label="Tipo de documento"
              value={form.type}
              onChange={(event) =>
                setForm({
                  ...form,
                  type: event.target.value as DocumentItem["type"],
                })
              }
            >
              <option>Ata</option>
              <option>Ofício</option>
              <option>Prestação de contas</option>
            </SelectField>
            <SelectField
              label="Modelo"
              value={form.templateId}
              onChange={(event) =>
                setForm({ ...form, templateId: event.target.value })
              }
            >
              <option value="">Sem modelo</option>
              {templates
                .filter((item) => item.type === form.type)
                .map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
            </SelectField>
          </div>
          <TextArea
            label="Informações para o documento"
            value={form.content}
            onChange={(event) => {
              setForm({ ...form, content: event.target.value })
              setError("")
            }}
            placeholder="Descreva os participantes, decisões, datas e demais informações relevantes..."
          />
          <div className="form-actions">
            <Button variant="secondary" onClick={() => submit("Rascunho")}>
              Salvar rascunho
            </Button>
            <Button icon="arrow" onClick={() => submit("Em validação")}>
              Enviar para validação
            </Button>
          </div>
        </section>
        <aside className="tips-card">
          <span>
            <Icon name="spark" />
          </span>
          <h3>Como funciona?</h3>
          <ol>
            <li>Escolha o tipo e um modelo.</li>
            <li>Insira apenas as informações necessárias.</li>
            <li>Revise antes de enviar para validação.</li>
          </ol>
          <small>
            O conteúdo deste protótipo será integrado ao pipeline de IA em
            apps/server.
          </small>
        </aside>
      </div>
    </>
  )
}
