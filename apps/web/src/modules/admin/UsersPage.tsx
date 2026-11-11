import { FormEvent, useState } from "react"
import { Icon } from "@/components/Icon"
import {
  Badge,
  Button,
  DataTable,
  EmptyState,
  Field,
  Modal,
  PageHeader,
  SelectField,
} from "@/components/ui"
import { initials } from "@/lib/formatters"
import type { CreateUserWithPasswordInput, Role, User } from "@/lib/types"

export interface UsersPageProps {
  users: User[]
  currentUser: User
  save: (user: CreateUserWithPasswordInput) => void
}

export function UsersPage({ users, currentUser, save }: UsersPageProps) {
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
        <DataTable
          caption="Equipe e funcionários vinculados à instituição"
          headers={["Funcionário", "Perfil", "Status", "Conta", ""]}
          hasRows={employees.length > 0}
          emptyState={
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
          }
        >
          {employees.map((user) => (
            <tr key={user.id}>
              <td>
                <div className="person-cell">
                  <span className="avatar avatar--small" aria-hidden="true">
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
                  type="button"
                  className="icon-button"
                  onClick={() => setModal(user)}
                  aria-label={`Editar funcionário ${user.name}`}
                >
                  <Icon name="edit" size={17} />
                </button>
              </td>
            </tr>
          ))}
        </DataTable>
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

interface UserModalProps {
  user?: User
  allUsers: User[]
  institutionId: string
  close: () => void
  submit: (user: CreateUserWithPasswordInput) => void
}

function UserModal({
  user,
  allUsers,
  institutionId,
  close,
  submit,
}: UserModalProps) {
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
    <Modal
      eyebrow="EQUIPE"
      title={user ? "Editar funcionário" : "Novo funcionário"}
      description="A conta será vinculada automaticamente à instituição ativa."
      onClose={close}
    >
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
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          error={errors.email}
        />
        <Field
          label={
            user ? "Nova senha (deixe em branco para manter)" : "Senha inicial"
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
              setForm({ ...form, status: event.target.value as User["status"] })
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
    </Modal>
  )
}
