import { FormEvent, useState } from "react"
import { Icon } from "@/components/Icon"
import { Brand, Button, Field, SelectField } from "@/components/ui"
import type {
  AuthView,
  CreateUserWithPasswordInput,
  Institution,
  Store,
} from "@/lib/types"

export function AuthFlow({
  view,
  setView,
  store,
  login,
  demoLogin,
  pendingInstitutionId,
  onInstitutionCreated,
  onAdminCreated,
}: {
  view: AuthView
  setView: (view: AuthView) => void
  store: Store
  login: (email: string, password: string) => boolean
  demoLogin: () => void
  pendingInstitutionId: string | null
  onInstitutionCreated: (institution: Institution) => void
  onAdminCreated: (user: CreateUserWithPasswordInput) => void
}) {
  return (
    <div className="auth">
      <section className="auth__story">
        <Brand light />
        <div className="auth__story-content">
          <span className="eyebrow eyebrow--light">
            <Icon name="spark" size={15} />
            Gestão pública mais simples
          </span>
          <h1>
            Documentos administrativos, <em>sem complicação.</em>
          </h1>
          <p>
            Crie, valide e acompanhe documentos institucionais em um só lugar,
            com rastreabilidade em cada etapa.
          </p>
          <div className="auth__features">
            <span>
              <Icon name="check" size={15} />
              Fluxos organizados
            </span>
            <span>
              <Icon name="check" size={15} />
              Auditoria completa
            </span>
            <span>
              <Icon name="check" size={15} />
              Dados por instituição
            </span>
          </div>
        </div>
        <small className="auth__legal">
          Ambiente de demonstração · Dados em memória (sem senhas armazenadas)
        </small>
      </section>
      <section className="auth__panel">
        <div className="auth__mobile-brand">
          <Brand />
        </div>
        {view === "welcome" && (
          <Welcome setView={setView} demoLogin={demoLogin} />
        )}
        {view === "login" && (
          <Login setView={setView} login={login} demoLogin={demoLogin} />
        )}
        {view === "institution" && (
          <InstitutionSignup
            store={store}
            setView={setView}
            submit={onInstitutionCreated}
          />
        )}
        {view === "first-user" && pendingInstitutionId && (
          <FirstUserSignup
            store={store}
            institutionId={pendingInstitutionId}
            submit={onAdminCreated}
          />
        )}
      </section>
    </div>
  )
}

function Welcome({
  setView,
  demoLogin,
}: {
  setView: (view: AuthView) => void
  demoLogin: () => void
}) {
  return (
    <div className="auth-card">
      <span className="eyebrow">BEM-VINDO AO DOCFLOW</span>
      <h2>Como deseja começar?</h2>
      <p className="muted">
        Acesse sua conta ou cadastre sua instituição para organizar os processos
        administrativos.
      </p>
      <div className="choice-list">
        <button
          className="choice-card choice-card--primary"
          onClick={() => setView("login")}
        >
          <span className="choice-card__icon">
            <Icon name="arrow" />
          </span>
          <span>
            <strong>Entrar na minha conta</strong>
            <small>Acesse documentos e tarefas da sua instituição</small>
          </span>
          <Icon name="chevron" />
        </button>
        <button className="choice-card" onClick={() => setView("institution")}>
          <span className="choice-card__icon">
            <Icon name="building" />
          </span>
          <span>
            <strong>Cadastrar uma instituição</strong>
            <small>Crie um novo espaço para sua equipe</small>
          </span>
          <Icon name="chevron" />
        </button>
      </div>
      <DemoAccess onClick={demoLogin} />
    </div>
  )
}

function DemoAccess({ onClick }: { onClick: () => void }) {
  return (
    <div className="demo-box">
      <span className="demo-box__icon">
        <Icon name="spark" size={18} />
      </span>
      <span>
        <strong>Quer conhecer antes?</strong>
        <small>Explore o sistema com dados fictícios.</small>
      </span>
      <Button variant="secondary" onClick={onClick}>
        Acessar demonstração
      </Button>
    </div>
  )
}

function Login({
  setView,
  login,
  demoLogin,
}: {
  setView: (view: AuthView) => void
  login: (email: string, password: string) => boolean
  demoLogin: () => void
}) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!login(email, password)) {
      setError(
        "E-mail ou senha inválidos. Verifique os dados e tente novamente.",
      )
    }
  }

  return (
    <div className="auth-card">
      <button className="back-link" onClick={() => setView("welcome")}>
        ← Voltar
      </button>
      <span className="eyebrow">ACESSO À CONTA</span>
      <h2>Entre para continuar</h2>
      <p className="muted">Use as credenciais vinculadas à sua instituição.</p>
      <form className="form-stack" onSubmit={submit}>
        {error && <div className="form-alert">{error}</div>}
        <Field
          label="E-mail"
          type="email"
          placeholder="voce@instituicao.org"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value)
            setError("")
          }}
          required
        />
        <Field
          label="Senha"
          type="password"
          placeholder="Digite sua senha"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value)
            setError("")
          }}
          required
        />
        <Button type="submit" className="button--full" icon="arrow">
          Entrar
        </Button>
      </form>
      <p className="auth-switch">
        Ainda não tem uma conta?{" "}
        <button onClick={() => setView("institution")}>
          Cadastre sua instituição
        </button>
      </p>
      <DemoAccess onClick={demoLogin} />
    </div>
  )
}

function InstitutionSignup({
  store,
  setView,
  submit,
}: {
  store: Store
  setView: (view: AuthView) => void
  submit: (institution: Institution) => void
}) {
  const [form, setForm] = useState({
    name: "",
    type: "Escola" as Institution["type"],
    cnpj: "",
    email: "",
    phone: "",
    address: "",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = "Informe o nome da instituição."
    if (!form.email.trim()) next.email = "Informe o e-mail institucional."
    else if (!/\S+@\S+\.\S+/.test(form.email))
      next.email = "Informe um e-mail válido."
    if (
      store.institutions.some(
        (item) => item.email.toLowerCase() === form.email.toLowerCase(),
      )
    ) {
      next.email = "Já existe uma instituição com este e-mail."
    }
    setErrors(next)
    if (Object.keys(next).length) return
    submit({
      id: crypto.randomUUID(),
      ...form,
      name: form.name.trim(),
      email: form.email.trim(),
    })
  }

  return (
    <div className="auth-card auth-card--wide">
      <button className="back-link" onClick={() => setView("welcome")}>
        ← Voltar
      </button>
      <div className="step">
        <span className="step__active">1</span>
        <i />
        <span>2</span>
        <small>Instituição</small>
        <small>Administrador</small>
      </div>
      <span className="eyebrow">NOVA INSTITUIÇÃO</span>
      <h2>Conte sobre sua instituição</h2>
      <p className="muted">
        Estes dados identificam o espaço de trabalho da sua equipe.
      </p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="field--span">
          <Field
            label="Nome da instituição"
            placeholder="Ex.: Escola Municipal Horizonte"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            error={errors.name}
          />
        </div>
        <SelectField
          label="Tipo de instituição"
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
          placeholder="00.000.000/0000-00"
          value={form.cnpj}
          onChange={(event) => setForm({ ...form, cnpj: event.target.value })}
        />
        <Field
          label="E-mail institucional"
          type="email"
          placeholder="contato@instituicao.org"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          error={errors.email}
        />
        <Field
          label="Telefone"
          optional
          placeholder="(00) 0000-0000"
          value={form.phone}
          onChange={(event) => setForm({ ...form, phone: event.target.value })}
        />
        <div className="field--span">
          <Field
            label="Endereço"
            optional
            placeholder="Rua, número, bairro, cidade e estado"
            value={form.address}
            onChange={(event) =>
              setForm({ ...form, address: event.target.value })
            }
          />
        </div>
        <div className="form-actions field--span">
          <Button variant="secondary" onClick={() => setView("welcome")}>
            Cancelar
          </Button>
          <Button type="submit" icon="arrow">
            Continuar
          </Button>
        </div>
      </form>
    </div>
  )
}

function FirstUserSignup({
  store,
  institutionId,
  submit,
}: {
  store: Store
  institutionId: string
  submit: (user: CreateUserWithPasswordInput) => void
}) {
  const institution = store.institutions.find(
    (item) => item.id === institutionId,
  )
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = "Informe seu nome completo."
    if (!/\S+@\S+\.\S+/.test(form.email))
      next.email = "Informe um e-mail válido."
    if (
      store.users.some(
        (item) =>
          item.institutionId === institutionId &&
          item.email.toLowerCase() === form.email.toLowerCase(),
      )
    ) {
      next.email = "Este e-mail já está em uso."
    }
    if (form.password.length < 6) next.password = "Use pelo menos 6 caracteres."
    if (form.confirm !== form.password)
      next.confirm = "As senhas não coincidem."
    setErrors(next)
    if (Object.keys(next).length) return
    submit({
      id: crypto.randomUUID(),
      institutionId,
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
      role: "Administrador da instituição",
      status: "Ativo",
    })
  }

  return (
    <div className="auth-card auth-card--wide">
      <div className="step">
        <span>✓</span>
        <i />
        <span className="step__active">2</span>
        <small>Instituição</small>
        <small>Administrador</small>
      </div>
      <span className="eyebrow">PRIMEIRO ACESSO</span>
      <h2>Crie sua conta de administrador</h2>
      <p className="muted">
        Você será responsável por gerenciar <strong>{institution?.name}</strong>{" "}
        e a equipe vinculada.
      </p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="field--span">
          <Field
            label="Nome completo"
            placeholder="Seu nome e sobrenome"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            error={errors.name}
          />
        </div>
        <div className="field--span">
          <Field
            label="E-mail de acesso"
            type="email"
            placeholder="voce@instituicao.org"
            value={form.email}
            onChange={(event) =>
              setForm({ ...form, email: event.target.value })
            }
            error={errors.email}
          />
        </div>
        <Field
          label="Senha"
          type="password"
          placeholder="Mínimo de 6 caracteres"
          value={form.password}
          onChange={(event) =>
            setForm({ ...form, password: event.target.value })
          }
          error={errors.password}
        />
        <Field
          label="Confirme a senha"
          type="password"
          placeholder="Digite novamente"
          value={form.confirm}
          onChange={(event) =>
            setForm({ ...form, confirm: event.target.value })
          }
          error={errors.confirm}
        />
        <div className="role-note field--span">
          <Icon name="shield" size={20} />
          <span>
            <strong>Administrador da instituição</strong>
            <small>Este perfil poderá gerenciar dados e funcionários.</small>
          </span>
        </div>
        <div className="form-actions field--span">
          <Button type="submit" icon="arrow">
            Criar conta e acessar
          </Button>
        </div>
      </form>
    </div>
  )
}
