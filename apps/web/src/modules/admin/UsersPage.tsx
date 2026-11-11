import { FormEvent, useState } from "react"
import { Icon } from "@/components/Icon"
import {
  Badge,
  Button,
  EmptyState,
  Field,
  PageHeader,
  SelectField,
} from "@/components/ui"
import { initials } from "@/lib/formatters"
import type { CreateUserWithPasswordInput, Role, User } from "@/lib/types"

export function UsersPage({
  users,
  currentUser,
  save,
}: {
  users: User[]
  currentUser: User
  save: (user: CreateUserWithPasswordInput) => void
}) {
  const employees = users.filter((user) => user.id !== currentUser.id)
  const [modal, setModal] = useState<User | "new" | null>(null)

  return (
    <>
      <PageHeader
        eyebrow="FUNCIONÁRIOS"
        title="Equipe da instituição"
        description="Gerencie as pessoas e os perfis vinculados à instituição ativa."
        action={
          <Button icon="plus" onClick={() => setModal("new")}>
            Novo funcionário
          </Button>
        }
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Funcionário</th>
                <th>Perfil</th>
                <th>Status</th>
                <th>Conta</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {employees.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="person-cell">
                      <span className="avatar avatar--small">
                        {initials(user.name)}
                      </span>
                      <span>
                        <strong>{user.name}</strong>
                        <small>{user.email}</small>
                      </span>
                    </div>
                  </td>
                  <td>{user.role}</td>
                  <td>
                    <Badge status={user.status} />
                  </td>
                  <td>Credencial protegida</td>
                  <td>
                    <button
                      className="icon-button"
                      onClick={() => setModal(user)}
                      aria-label="Editar funcionário"
                    >
                      <Icon name="edit" size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!employees.length && (
          <EmptyState
            icon="users"
            title="Sua equipe começa aqui"
            description="Cadastre o primeiro funcionário vinculado a esta instituição."
            action={
              <Button icon="plus" onClick={() => setModal("new")}>
                Cadastrar funcionário
              </Button>
            }
          />
        )}
      </section>
      {modal && (
        <UserModal
          user={modal === "new" ? undefined : modal}
          allUsers={users}
          institutionId={currentUser.institutionId}
          close={() => setModal(null)}
          submit={(user) => {
            save(user)
            setModal(null)
          }}
        />
      )}
    </>
  )
}

function UserModal({
  user,
  allUsers,
  institutionId,
  close,
  submit,
}: {
  user?: User
  allUsers: User[]
  institutionId: string
  close: () => void
  submit: (user: CreateUserWithPasswordInput) => void
}) {
  const [form, setForm] = useState({
    name: user?.name || "",
    email: user?.email || "",
    password: "",
    role: user?.role || "Funcionário" as Role,
    status: user?.status || "Ativo" as User["status"],
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = "Informe o nome."
    if (!/\S+@\S+\.\S+/.test(form.email))
      next.email = "Informe um e-mail válido."
    if (
      allUsers.some(
        (item) =>
          item.id !== user?.id &&
          item.email.toLowerCase() === form.email.toLowerCase(),
      )
    ) {
      next.email = "Este e-mail já está cadastrado nesta instituição."
    }
    if (!user && form.password.length < 6) {
      next.password = "Use pelo menos 6 caracteres."
    } else if (user && form.password && form.password.length < 6) {
      next.password = "Use pelo menos 6 caracteres."
    }
    setErrors(next)
    if (Object.keys(next).length) return
    submit({
      id: user?.id || crypto.randomUUID(),
      institutionId,
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password || undefined,
      role: form.role,
      status: form.status,
    })
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal__header">
          <div>
            <span className="eyebrow">EQUIPE</span>
            <h2>{user ? "Editar funcionário" : "Novo funcionário"}</h2>
          </div>
          <button className="icon-button" onClick={close} aria-label="Fechar">
            <Icon name="close" />
          </button>
        </div>
        <p className="muted">
          A conta será vinculada automaticamente à instituição ativa.
        </p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <Field
            label="Nome completo"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            error={errors.name}
          />
          <Field
            label="E-mail"
            type="email"
            value={form.email}
            onChange={(event) =>
              setForm({ ...form, email: event.target.value })
            }
            error={errors.email}
          />
          <Field
            label={
              user
                ? "Nova senha (deixe em branco para manter)"
                : "Senha inicial"
            }
            optional={Boolean(user)}
            type="password"
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
            error={errors.password}
          />
          <div className="form-grid">
            <SelectField
              label="Perfil de acesso"
              value={form.role}
              onChange={(event) =>
                setForm({ ...form, role: event.target.value as Role })
              }
            >
              <option>Funcionário</option>
              <option>Administrador da instituição</option>
            </SelectField>
            <SelectField
              label="Status da conta"
              value={form.status}
              onChange={(event) =>
                setForm({
                  ...form,
                  status: event.target.value as User["status"],
                })
              }
            >
              <option>Ativo</option>
              <option>Inativo</option>
            </SelectField>
          </div>
          <div className="form-actions">
            <Button variant="secondary" onClick={close}>
              Cancelar
            </Button>
            <Button type="submit">
              {user ? "Salvar alterações" : "Cadastrar funcionário"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
