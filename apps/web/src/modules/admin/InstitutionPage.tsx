import { useState } from "react"
import { Icon } from "@/components/Icon"
import { Button, Field, PageHeader, SelectField } from "@/components/ui"
import type { Institution } from "@/lib/types"

export function InstitutionPage({
  institution,
  isAdmin,
  save,
}: {
  institution: Institution
  isAdmin: boolean
  save: (item: Institution) => void
}) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(institution)

  return (
    <>
      <PageHeader
        eyebrow="INSTITUIÇÃO"
        title="Dados institucionais"
        description="Informações do espaço de trabalho ativo."
        action={
          isAdmin && !editing ? (
            <Button
              variant="secondary"
              icon="edit"
              onClick={() => setEditing(true)}
            >
              Editar dados
            </Button>
          ) : undefined
        }
      />
      <section className="panel institution-card">
        <div className="institution-card__heading">
          <span>
            <Icon name="building" size={28} />
          </span>
          <div>
            <h2>{institution.name}</h2>
            <p>{institution.type}</p>
          </div>
        </div>
        {editing ? (
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault()
              save(form)
              setEditing(false)
            }}
          >
            <div className="field--span">
              <Field
                label="Nome da instituição"
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
              />
            </div>
            <SelectField
              label="Tipo"
              value={form.type}
              onChange={(event) =>
                setForm({
                  ...form,
                  type: event.target.value as Institution["type"],
                })
              }
            >
              <option>Escola</option>
              <option>Outra instituição</option>
            </SelectField>
            <Field
              label="CNPJ"
              optional
              value={form.cnpj}
              onChange={(event) =>
                setForm({ ...form, cnpj: event.target.value })
              }
            />
            <Field
              label="E-mail institucional"
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm({ ...form, email: event.target.value })
              }
            />
            <Field
              label="Telefone"
              optional
              value={form.phone}
              onChange={(event) =>
                setForm({ ...form, phone: event.target.value })
              }
            />
            <div className="field--span">
              <Field
                label="Endereço"
                optional
                value={form.address}
                onChange={(event) =>
                  setForm({ ...form, address: event.target.value })
                }
              />
            </div>
            <div className="form-actions field--span">
              <Button
                variant="secondary"
                onClick={() => {
                  setForm(institution)
                  setEditing(false)
                }}
              >
                Cancelar
              </Button>
              <Button type="submit">Salvar alterações</Button>
            </div>
          </form>
        ) : (
          <dl className="details-grid">
            <div>
              <dt>CNPJ</dt>
              <dd>{institution.cnpj || "Não informado"}</dd>
            </div>
            <div>
              <dt>E-mail institucional</dt>
              <dd>{institution.email}</dd>
            </div>
            <div>
              <dt>Telefone</dt>
              <dd>{institution.phone || "Não informado"}</dd>
            </div>
            <div>
              <dt>Endereço</dt>
              <dd>{institution.address || "Não informado"}</dd>
            </div>
          </dl>
        )}
        {!isAdmin && (
          <div className="info-note">
            <Icon name="shield" size={18} />
            Somente administradores podem editar estes dados.
          </div>
        )}
      </section>
    </>
  )
}
