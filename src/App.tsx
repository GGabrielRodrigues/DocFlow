import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react'

type Role = 'Administrador da instituição' | 'Funcionário'
type Page = 'dashboard' | 'documents' | 'create' | 'templates' | 'validations' | 'audit' | 'institution' | 'users'
type AuthView = 'welcome' | 'login' | 'institution' | 'first-user'
type DocumentStatus = 'Rascunho' | 'Em validação' | 'Aprovado' | 'Devolvido'

type Institution = {
  id: string
  name: string
  type: 'Escola' | 'Outra instituição'
  cnpj: string
  email: string
  phone: string
  address: string
}

type User = {
  id: string
  institutionId: string
  name: string
  email: string
  password: string
  role: Role
  status: 'Ativo' | 'Inativo'
}

type DocumentItem = {
  id: string
  institutionId: string
  title: string
  type: 'Ata' | 'Ofício' | 'Prestação de contas'
  content: string
  status: DocumentStatus
  authorId: string
  updatedAt: string
}

type Template = {
  id: string
  institutionId: string
  name: string
  type: DocumentItem['type']
  description: string
}

type Audit = {
  id: string
  institutionId: string
  userId: string
  action: string
  detail: string
  date: string
}

type Store = {
  institutions: Institution[]
  users: User[]
  documents: DocumentItem[]
  templates: Template[]
  audits: Audit[]
}

const DEMO_INSTITUTION = 'inst-demo'
const DEMO_ADMIN = 'user-demo-admin'
const STORAGE_KEY = 'docflow-prototype-v2'
const SESSION_KEY = 'docflow-session-v2'

const initialStore: Store = {
  institutions: [
    {
      id: DEMO_INSTITUTION,
      name: 'Escola Municipal Horizonte',
      type: 'Escola',
      cnpj: '12.345.678/0001-90',
      email: 'contato@horizonte.edu.br',
      phone: '(61) 3333-2040',
      address: 'Quadra 12, Área Especial — Brasília, DF',
    },
  ],
  users: [
    {
      id: DEMO_ADMIN,
      institutionId: DEMO_INSTITUTION,
      name: 'Marina Carvalho',
      email: 'marina@demo.com',
      password: 'demo123',
      role: 'Administrador da instituição',
      status: 'Ativo',
    },
    {
      id: 'user-demo-employee',
      institutionId: DEMO_INSTITUTION,
      name: 'Rafael Nunes',
      email: 'rafael@horizonte.edu.br',
      password: 'demo123',
      role: 'Funcionário',
      status: 'Ativo',
    },
  ],
  documents: [
    {
      id: 'doc-1',
      institutionId: DEMO_INSTITUTION,
      title: 'Ata da reunião pedagógica — Maio',
      type: 'Ata',
      content: 'Registro da reunião pedagógica mensal com a equipe docente.',
      status: 'Aprovado',
      authorId: DEMO_ADMIN,
      updatedAt: '2025-05-22T14:30:00.000Z',
    },
    {
      id: 'doc-2',
      institutionId: DEMO_INSTITUTION,
      title: 'Ofício de solicitação de materiais',
      type: 'Ofício',
      content: 'Solicitação de materiais para as atividades do segundo semestre.',
      status: 'Em validação',
      authorId: 'user-demo-employee',
      updatedAt: '2025-05-24T10:15:00.000Z',
    },
    {
      id: 'doc-3',
      institutionId: DEMO_INSTITUTION,
      title: 'Prestação de contas — Abril',
      type: 'Prestação de contas',
      content: 'Consolidação das despesas e comprovantes do mês de abril.',
      status: 'Rascunho',
      authorId: DEMO_ADMIN,
      updatedAt: '2025-05-25T08:40:00.000Z',
    },
  ],
  templates: [
    { id: 'tpl-1', institutionId: DEMO_INSTITUTION, name: 'Ata de reunião', type: 'Ata', description: 'Modelo para reuniões pedagógicas e administrativas.' },
    { id: 'tpl-2', institutionId: DEMO_INSTITUTION, name: 'Ofício institucional', type: 'Ofício', description: 'Comunicação oficial com órgãos e fornecedores.' },
    { id: 'tpl-3', institutionId: DEMO_INSTITUTION, name: 'Prestação mensal', type: 'Prestação de contas', description: 'Resumo financeiro com despesas e comprovantes.' },
  ],
  audits: [
    { id: 'audit-1', institutionId: DEMO_INSTITUTION, userId: 'user-demo-employee', action: 'Documento encaminhado', detail: 'Ofício de solicitação de materiais enviado para validação', date: '2025-05-24T10:15:00.000Z' },
    { id: 'audit-2', institutionId: DEMO_INSTITUTION, userId: DEMO_ADMIN, action: 'Documento aprovado', detail: 'Ata da reunião pedagógica — Maio', date: '2025-05-22T14:30:00.000Z' },
  ],
}

const navItems: { id: Page; label: string; icon: IconName; adminOnly?: boolean }[] = [
  { id: 'dashboard', label: 'Visão geral', icon: 'grid' },
  { id: 'documents', label: 'Documentos', icon: 'file' },
  { id: 'create', label: 'Novo documento', icon: 'plus' },
  { id: 'templates', label: 'Modelos', icon: 'layers' },
  { id: 'validations', label: 'Validações', icon: 'check' },
  { id: 'audit', label: 'Auditoria', icon: 'history' },
  { id: 'institution', label: 'Instituição', icon: 'building' },
  { id: 'users', label: 'Funcionários', icon: 'users', adminOnly: true },
]

type IconName = 'grid' | 'file' | 'plus' | 'layers' | 'check' | 'history' | 'building' | 'users' | 'arrow' | 'logout' | 'menu' | 'close' | 'edit' | 'search' | 'shield' | 'spark' | 'chevron' | 'clock'

const iconPaths: Record<IconName, ReactNode> = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/></>,
  plus: <><path d="M12 5v14M5 12h14"/></>,
  layers: <><path d="m12 2 9 5-9 5-9-5 9-5z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/></>,
  check: <><path d="m20 6-11 11-5-5"/></>,
  history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></>,
  building: <><path d="M3 21h18M6 21V4h12v17M9 8h2M13 8h2M9 12h2M13 12h2M9 16h2M13 16h2"/></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M8.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M17 11a4 4 0 0 0 0-8M23 21v-2a4 4 0 0 0-3-3.87"/></>,
  arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
  close: <><path d="M18 6 6 18M6 6l12 12"/></>,
  edit: <><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z"/></>,
  search: <><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></>,
  shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></>,
  spark: <><path d="m12 3-1.4 4.2a5 5 0 0 1-3.2 3.2L3 12l4.4 1.6a5 5 0 0 1 3.2 3.2L12 21l1.4-4.2a5 5 0 0 1 3.2-3.2L21 12l-4.4-1.6a5 5 0 0 1-3.2-3.2z"/></>,
  chevron: <><path d="m9 18 6-6-6-6"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
}

function Icon({ name, size = 19 }: { name: IconName; size?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{iconPaths[name]}</svg>
}

function Button({ children, variant = 'primary', icon, type = 'button', onClick, disabled, className = '' }: {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  icon?: IconName
  type?: 'button' | 'submit'
  onClick?: () => void
  disabled?: boolean
  className?: string
}) {
  return <button className={`button button--${variant} ${className}`} type={type} onClick={onClick} disabled={disabled}>{icon && <Icon name={icon} size={17}/>}<span>{children}</span></button>
}

function Field({ label, error, optional, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; optional?: boolean }) {
  return <label className="field"><span className="field__label">{label}{optional && <small>Opcional</small>}</span><input className={error ? 'input input--error' : 'input'} {...props}/>{error && <span className="field__error">{error}</span>}</label>
}

function SelectField({ label, children, value, onChange, disabled }: { label: string; children: ReactNode; value: string; onChange: React.ChangeEventHandler<HTMLSelectElement>; disabled?: boolean }) {
  return <label className="field"><span className="field__label">{label}</span><span className="select-wrap"><select className="input" value={value} onChange={onChange} disabled={disabled}>{children}</select><Icon name="chevron" size={15}/></span></label>
}

function TextArea({ label, value, onChange, placeholder }: { label: string; value: string; onChange: React.ChangeEventHandler<HTMLTextAreaElement>; placeholder?: string }) {
  return <label className="field"><span className="field__label">{label}</span><textarea className="input textarea" value={value} onChange={onChange} placeholder={placeholder}/></label>
}

function Badge({ status }: { status: DocumentStatus | User['status'] }) {
  const key = status.toLowerCase().replace(' ', '-').replace('ç', 'c')
  return <span className={`badge badge--${key}`}><i/>{status}</span>
}

function Brand({ light = false }: { light?: boolean }) {
  return <div className={`brand ${light ? 'brand--light' : ''}`}><span className="brand__mark"><Icon name="file" size={22}/></span><span><strong>DocFlow</strong><small>Gestão administrativa</small></span></div>
}

function readStore(): Store {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : initialStore
  } catch {
    return initialStore
  }
}

function App() {
  const [store, setStore] = useState<Store>(readStore)
  const [currentUserId, setCurrentUserId] = useState<string | null>(() => localStorage.getItem(SESSION_KEY))
  const [authView, setAuthView] = useState<AuthView>('welcome')
  const [pendingInstitutionId, setPendingInstitutionId] = useState<string | null>(null)
  const [page, setPage] = useState<Page>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [toast, setToast] = useState('')

  useEffect(() => localStorage.setItem(STORAGE_KEY, JSON.stringify(store)), [store])
  useEffect(() => {
    if (currentUserId) localStorage.setItem(SESSION_KEY, currentUserId)
    else localStorage.removeItem(SESSION_KEY)
  }, [currentUserId])
  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  const currentUser = store.users.find(user => user.id === currentUserId && user.status === 'Ativo')
  const institution = currentUser ? store.institutions.find(item => item.id === currentUser.institutionId) : undefined

  const notify = (message: string) => setToast(message)
  const saveStore = (updater: (value: Store) => Store) => setStore(updater)
  const audit = (user: User, action: string, detail: string) => {
    saveStore(value => ({
      ...value,
      audits: [{ id: crypto.randomUUID(), institutionId: user.institutionId, userId: user.id, action, detail, date: new Date().toISOString() }, ...value.audits],
    }))
  }

  const login = (email: string, password: string) => {
    const user = store.users.find(item => item.email.toLowerCase() === email.trim().toLowerCase() && item.password === password && item.status === 'Ativo')
    if (!user) return false
    setCurrentUserId(user.id)
    setPage('dashboard')
    audit(user, 'Acesso realizado', 'Usuário entrou na aplicação')
    return true
  }

  const demoLogin = () => {
    setCurrentUserId(DEMO_ADMIN)
    setPage('dashboard')
    const demo = store.users.find(user => user.id === DEMO_ADMIN)
    if (demo) audit(demo, 'Acesso demonstrativo', 'Sessão de demonstração iniciada')
  }

  const logout = () => {
    if (currentUser) audit(currentUser, 'Sessão encerrada', 'Usuário saiu da aplicação')
    setCurrentUserId(null)
    setAuthView('welcome')
    setSidebarOpen(false)
  }

  if (!currentUser || !institution) {
    return <AuthFlow
      view={authView}
      setView={setAuthView}
      store={store}
      login={login}
      demoLogin={demoLogin}
      pendingInstitutionId={pendingInstitutionId}
      onInstitutionCreated={(newInstitution) => {
        saveStore(value => ({ ...value, institutions: [...value.institutions, newInstitution] }))
        setPendingInstitutionId(newInstitution.id)
        setAuthView('first-user')
      }}
      onAdminCreated={(user) => {
        saveStore(value => ({
          ...value,
          users: [...value.users, user],
          templates: [
            ...value.templates,
            { id: crypto.randomUUID(), institutionId: user.institutionId, name: 'Ata de reunião', type: 'Ata', description: 'Modelo base para reuniões administrativas.' },
            { id: crypto.randomUUID(), institutionId: user.institutionId, name: 'Ofício institucional', type: 'Ofício', description: 'Modelo para comunicações oficiais.' },
          ],
          audits: [{ id: crypto.randomUUID(), institutionId: user.institutionId, userId: user.id, action: 'Conta criada', detail: 'Primeiro administrador da instituição cadastrado', date: new Date().toISOString() }, ...value.audits],
        }))
        setCurrentUserId(user.id)
        setPage('dashboard')
        setPendingInstitutionId(null)
        notify('Instituição e conta criadas com sucesso.')
      }}
    />
  }

  const scopedDocuments = store.documents.filter(item => item.institutionId === institution.id)
  const scopedUsers = store.users.filter(item => item.institutionId === institution.id)
  const scopedTemplates = store.templates.filter(item => item.institutionId === institution.id)
  const scopedAudits = store.audits.filter(item => item.institutionId === institution.id)
  const isAdmin = currentUser.role === 'Administrador da instituição'

  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : ''}`}>
      <div className="sidebar__top"><Brand light/><button className="icon-button sidebar__close" onClick={() => setSidebarOpen(false)} aria-label="Fechar menu"><Icon name="close"/></button></div>
      <nav className="nav">
        <span className="nav__label">MENU PRINCIPAL</span>
        {navItems.filter(item => !item.adminOnly || isAdmin).map(item => <button key={item.id} className={`nav__item ${page === item.id ? 'nav__item--active' : ''}`} onClick={() => { setPage(item.id); setSidebarOpen(false) }}><Icon name={item.icon}/><span>{item.label}</span>{item.id === 'validations' && scopedDocuments.filter(doc => doc.status === 'Em validação').length > 0 && <b>{scopedDocuments.filter(doc => doc.status === 'Em validação').length}</b>}</button>)}
      </nav>
      <div className="sidebar__notice"><Icon name="shield" size={18}/><span><strong>Protótipo demonstrativo</strong><small>Autenticação e dados simulados.</small></span></div>
      <button className="sidebar__profile" onClick={logout}><span className="avatar">{initials(currentUser.name)}</span><span><strong>{currentUser.name}</strong><small>{shortRole(currentUser.role)}</small></span><Icon name="logout" size={18}/></button>
    </aside>
    {sidebarOpen && <button className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} aria-label="Fechar menu"/>}
    <main className="main">
      <header className="topbar">
        <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Abrir menu"><Icon name="menu"/></button>
        <div className="topbar__institution"><span className="topbar__icon"><Icon name="building" size={18}/></span><span><small>INSTITUIÇÃO ATIVA</small><strong>{institution.name}</strong></span></div>
        <div className="topbar__user"><span><small>Olá,</small><strong>{firstName(currentUser.name)}</strong></span><span className="avatar avatar--small">{initials(currentUser.name)}</span></div>
      </header>
      <div className="content">
        {page === 'dashboard' && <Dashboard documents={scopedDocuments} users={scopedUsers} audits={scopedAudits} allUsers={store.users} user={currentUser} institution={institution} onNavigate={setPage}/>}
        {page === 'documents' && <Documents documents={scopedDocuments} users={store.users} onNavigate={setPage}/>}
        {page === 'create' && <DocumentForm templates={scopedTemplates} user={currentUser} save={(doc) => {
          saveStore(value => ({ ...value, documents: [doc, ...value.documents], audits: [{ id: crypto.randomUUID(), institutionId: currentUser.institutionId, userId: currentUser.id, action: doc.status === 'Em validação' ? 'Documento encaminhado' : 'Documento criado', detail: doc.title, date: new Date().toISOString() }, ...value.audits] }))
          notify(doc.status === 'Em validação' ? 'Documento enviado para validação.' : 'Rascunho salvo com sucesso.')
          setPage('documents')
        }}/>}
        {page === 'templates' && <Templates templates={scopedTemplates} onUse={() => setPage('create')}/>}
        {page === 'validations' && <Validations documents={scopedDocuments} users={store.users} isAdmin={isAdmin} update={(id, status) => {
          const doc = store.documents.find(item => item.id === id)
          saveStore(value => ({
            ...value,
            documents: value.documents.map(item => item.id === id ? { ...item, status, updatedAt: new Date().toISOString() } : item),
            audits: [{ id: crypto.randomUUID(), institutionId: currentUser.institutionId, userId: currentUser.id, action: status === 'Aprovado' ? 'Documento aprovado' : 'Documento devolvido', detail: doc?.title || 'Documento', date: new Date().toISOString() }, ...value.audits],
          }))
          notify(status === 'Aprovado' ? 'Documento aprovado.' : 'Documento devolvido ao responsável.')
        }}/>}
        {page === 'audit' && <AuditPage audits={scopedAudits} users={store.users}/>}
        {page === 'institution' && <InstitutionPage institution={institution} isAdmin={isAdmin} save={(updated) => {
          saveStore(value => ({ ...value, institutions: value.institutions.map(item => item.id === updated.id ? updated : item) }))
          audit(currentUser, 'Instituição atualizada', 'Dados básicos da instituição foram alterados')
          notify('Dados da instituição atualizados.')
        }}/>}
        {page === 'users' && isAdmin && <UsersPage users={scopedUsers} currentUser={currentUser} save={(user) => {
          const exists = store.users.some(item => item.id === user.id)
          saveStore(value => ({ ...value, users: exists ? value.users.map(item => item.id === user.id ? user : item) : [...value.users, user] }))
          audit(currentUser, exists ? 'Funcionário atualizado' : 'Funcionário cadastrado', user.name)
          notify(exists ? 'Funcionário atualizado.' : 'Funcionário cadastrado com sucesso.')
        }}/>}
      </div>
    </main>
    {toast && <div className="toast"><span><Icon name="check" size={16}/></span>{toast}</div>}
  </div>
}

function AuthFlow({ view, setView, store, login, demoLogin, pendingInstitutionId, onInstitutionCreated, onAdminCreated }: {
  view: AuthView
  setView: (view: AuthView) => void
  store: Store
  login: (email: string, password: string) => boolean
  demoLogin: () => void
  pendingInstitutionId: string | null
  onInstitutionCreated: (institution: Institution) => void
  onAdminCreated: (user: User) => void
}) {
  return <div className="auth">
    <section className="auth__story">
      <Brand light/>
      <div className="auth__story-content">
        <span className="eyebrow eyebrow--light"><Icon name="spark" size={15}/>Gestão pública mais simples</span>
        <h1>Documentos administrativos, <em>sem complicação.</em></h1>
        <p>Crie, valide e acompanhe documentos institucionais em um só lugar, com rastreabilidade em cada etapa.</p>
        <div className="auth__features"><span><Icon name="check" size={15}/>Fluxos organizados</span><span><Icon name="check" size={15}/>Auditoria completa</span><span><Icon name="check" size={15}/>Dados por instituição</span></div>
      </div>
      <small className="auth__legal">Ambiente de demonstração · Dados e autenticação simulados</small>
    </section>
    <section className="auth__panel">
      <div className="auth__mobile-brand"><Brand/></div>
      {view === 'welcome' && <Welcome setView={setView} demoLogin={demoLogin}/>}
      {view === 'login' && <Login setView={setView} login={login} demoLogin={demoLogin}/>}
      {view === 'institution' && <InstitutionSignup store={store} setView={setView} submit={onInstitutionCreated}/>}
      {view === 'first-user' && pendingInstitutionId && <FirstUserSignup store={store} institutionId={pendingInstitutionId} submit={onAdminCreated}/>}
    </section>
  </div>
}

function Welcome({ setView, demoLogin }: { setView: (view: AuthView) => void; demoLogin: () => void }) {
  return <div className="auth-card">
    <span className="eyebrow">BEM-VINDO AO DOCFLOW</span>
    <h2>Como deseja começar?</h2>
    <p className="muted">Acesse sua conta ou cadastre sua instituição para organizar os processos administrativos.</p>
    <div className="choice-list">
      <button className="choice-card choice-card--primary" onClick={() => setView('login')}><span className="choice-card__icon"><Icon name="arrow"/></span><span><strong>Entrar na minha conta</strong><small>Acesse documentos e tarefas da sua instituição</small></span><Icon name="chevron"/></button>
      <button className="choice-card" onClick={() => setView('institution')}><span className="choice-card__icon"><Icon name="building"/></span><span><strong>Cadastrar uma instituição</strong><small>Crie um novo espaço para sua equipe</small></span><Icon name="chevron"/></button>
    </div>
    <DemoAccess onClick={demoLogin}/>
  </div>
}

function DemoAccess({ onClick }: { onClick: () => void }) {
  return <div className="demo-box"><span className="demo-box__icon"><Icon name="spark" size={18}/></span><span><strong>Quer conhecer antes?</strong><small>Explore o sistema com dados fictícios.</small></span><Button variant="secondary" onClick={onClick}>Acessar demonstração</Button></div>
}

function Login({ setView, login, demoLogin }: { setView: (view: AuthView) => void; login: (email: string, password: string) => boolean; demoLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!login(email, password)) setError('E-mail ou senha inválidos. Verifique os dados e tente novamente.')
  }
  return <div className="auth-card">
    <button className="back-link" onClick={() => setView('welcome')}>← Voltar</button>
    <span className="eyebrow">ACESSO À CONTA</span><h2>Entre para continuar</h2><p className="muted">Use as credenciais vinculadas à sua instituição.</p>
    <form className="form-stack" onSubmit={submit}>
      {error && <div className="form-alert">{error}</div>}
      <Field label="E-mail" type="email" placeholder="voce@instituicao.org" value={email} onChange={event => { setEmail(event.target.value); setError('') }} required/>
      <Field label="Senha" type="password" placeholder="Digite sua senha" value={password} onChange={event => { setPassword(event.target.value); setError('') }} required/>
      <Button type="submit" className="button--full" icon="arrow">Entrar</Button>
    </form>
    <p className="auth-switch">Ainda não tem uma conta? <button onClick={() => setView('institution')}>Cadastre sua instituição</button></p>
    <DemoAccess onClick={demoLogin}/>
  </div>
}

function InstitutionSignup({ store, setView, submit }: { store: Store; setView: (view: AuthView) => void; submit: (institution: Institution) => void }) {
  const [form, setForm] = useState({ name: '', type: 'Escola' as Institution['type'], cnpj: '', email: '', phone: '', address: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = 'Informe o nome da instituição.'
    if (!form.email.trim()) next.email = 'Informe o e-mail institucional.'
    else if (!/\S+@\S+\.\S+/.test(form.email)) next.email = 'Informe um e-mail válido.'
    if (store.institutions.some(item => item.email.toLowerCase() === form.email.toLowerCase())) next.email = 'Já existe uma instituição com este e-mail.'
    setErrors(next)
    if (Object.keys(next).length) return
    submit({ id: crypto.randomUUID(), ...form, name: form.name.trim(), email: form.email.trim() })
  }
  return <div className="auth-card auth-card--wide">
    <button className="back-link" onClick={() => setView('welcome')}>← Voltar</button>
    <div className="step"><span className="step__active">1</span><i/><span>2</span><small>Instituição</small><small>Administrador</small></div>
    <span className="eyebrow">NOVA INSTITUIÇÃO</span><h2>Conte sobre sua instituição</h2><p className="muted">Estes dados identificam o espaço de trabalho da sua equipe.</p>
    <form className="form-grid" onSubmit={handleSubmit}>
      <div className="field--span"><Field label="Nome da instituição" placeholder="Ex.: Escola Municipal Horizonte" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} error={errors.name}/></div>
      <SelectField label="Tipo de instituição" value={form.type} onChange={event => setForm({ ...form, type: event.target.value as Institution['type'] })}><option>Escola</option><option>Outra instituição</option></SelectField>
      <Field label="CNPJ" optional placeholder="00.000.000/0000-00" value={form.cnpj} onChange={event => setForm({ ...form, cnpj: event.target.value })}/>
      <Field label="E-mail institucional" type="email" placeholder="contato@instituicao.org" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })} error={errors.email}/>
      <Field label="Telefone" optional placeholder="(00) 0000-0000" value={form.phone} onChange={event => setForm({ ...form, phone: event.target.value })}/>
      <div className="field--span"><Field label="Endereço" optional placeholder="Rua, número, bairro, cidade e estado" value={form.address} onChange={event => setForm({ ...form, address: event.target.value })}/></div>
      <div className="form-actions field--span"><Button variant="secondary" onClick={() => setView('welcome')}>Cancelar</Button><Button type="submit" icon="arrow">Continuar</Button></div>
    </form>
  </div>
}

function FirstUserSignup({ store, institutionId, submit }: { store: Store; institutionId: string; submit: (user: User) => void }) {
  const institution = store.institutions.find(item => item.id === institutionId)
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = 'Informe seu nome completo.'
    if (!/\S+@\S+\.\S+/.test(form.email)) next.email = 'Informe um e-mail válido.'
    if (store.users.some(item => item.institutionId === institutionId && item.email.toLowerCase() === form.email.toLowerCase())) next.email = 'Este e-mail já está em uso.'
    if (form.password.length < 6) next.password = 'Use pelo menos 6 caracteres.'
    if (form.confirm !== form.password) next.confirm = 'As senhas não coincidem.'
    setErrors(next)
    if (Object.keys(next).length) return
    submit({ id: crypto.randomUUID(), institutionId, name: form.name.trim(), email: form.email.trim(), password: form.password, role: 'Administrador da instituição', status: 'Ativo' })
  }
  return <div className="auth-card auth-card--wide">
    <div className="step"><span>✓</span><i/><span className="step__active">2</span><small>Instituição</small><small>Administrador</small></div>
    <span className="eyebrow">PRIMEIRO ACESSO</span><h2>Crie sua conta de administrador</h2><p className="muted">Você será responsável por gerenciar <strong>{institution?.name}</strong> e a equipe vinculada.</p>
    <form className="form-grid" onSubmit={handleSubmit}>
      <div className="field--span"><Field label="Nome completo" placeholder="Seu nome e sobrenome" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} error={errors.name}/></div>
      <div className="field--span"><Field label="E-mail de acesso" type="email" placeholder="voce@instituicao.org" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })} error={errors.email}/></div>
      <Field label="Senha" type="password" placeholder="Mínimo de 6 caracteres" value={form.password} onChange={event => setForm({ ...form, password: event.target.value })} error={errors.password}/>
      <Field label="Confirme a senha" type="password" placeholder="Digite novamente" value={form.confirm} onChange={event => setForm({ ...form, confirm: event.target.value })} error={errors.confirm}/>
      <div className="role-note field--span"><Icon name="shield" size={20}/><span><strong>Administrador da instituição</strong><small>Este perfil poderá gerenciar dados e funcionários.</small></span></div>
      <div className="form-actions field--span"><Button type="submit" icon="arrow">Criar conta e acessar</Button></div>
    </form>
  </div>
}

function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>
}

function Dashboard({ documents, users, audits, allUsers, user, institution, onNavigate }: { documents: DocumentItem[]; users: User[]; audits: Audit[]; allUsers: User[]; user: User; institution: Institution; onNavigate: (page: Page) => void }) {
  const pending = documents.filter(doc => doc.status === 'Em validação').length
  const approved = documents.filter(doc => doc.status === 'Aprovado').length
  return <>
    <PageHeader eyebrow="PAINEL DA INSTITUIÇÃO" title={`Bom dia, ${firstName(user.name)}.`} description={`Acompanhe o que está acontecendo na ${institution.name}.`} action={<Button icon="plus" onClick={() => onNavigate('create')}>Novo documento</Button>}/>
    <div className="stats">
      <Stat icon="file" label="Documentos" value={documents.length} note="Total da instituição"/>
      <Stat icon="clock" label="Em validação" value={pending} note={pending ? 'Aguardando análise' : 'Nenhuma pendência'} accent="amber"/>
      <Stat icon="check" label="Aprovados" value={approved} note="Documentos concluídos" accent="green"/>
      <Stat icon="users" label="Pessoas" value={users.length} note="Contas vinculadas" accent="violet"/>
    </div>
    <div className="dashboard-grid">
      <section className="panel">
        <div className="panel__header"><div><h2>Documentos recentes</h2><p>Últimas movimentações da instituição</p></div><button className="text-link" onClick={() => onNavigate('documents')}>Ver todos <Icon name="arrow" size={15}/></button></div>
        <div className="document-list">{documents.slice(0, 4).map(doc => <DocumentRow key={doc.id} doc={doc} author={allUsers.find(item => item.id === doc.authorId)}/>)}
          {!documents.length && <EmptyState title="Nenhum documento criado" description="Crie o primeiro documento da sua instituição." action={<Button icon="plus" onClick={() => onNavigate('create')}>Criar documento</Button>}/>}
        </div>
      </section>
      <section className="panel">
        <div className="panel__header"><div><h2>Atividade recente</h2><p>Ações registradas em auditoria</p></div></div>
        <div className="timeline">{audits.slice(0, 5).map(item => <div className="timeline__item" key={item.id}><span className="timeline__dot"/><div><strong>{item.action}</strong><p>{item.detail}</p><small>{allUsers.find(entry => entry.id === item.userId)?.name || 'Usuário'} · {relativeDate(item.date)}</small></div></div>)}
          {!audits.length && <p className="empty-line">As atividades aparecerão aqui.</p>}
        </div>
      </section>
    </div>
  </>
}

function Stat({ icon, label, value, note, accent = 'blue' }: { icon: IconName; label: string; value: number; note: string; accent?: string }) {
  return <div className="stat"><span className={`stat__icon stat__icon--${accent}`}><Icon name={icon}/></span><span className="stat__value">{String(value).padStart(2, '0')}</span><strong>{label}</strong><small>{note}</small></div>
}

function Documents({ documents, users, onNavigate }: { documents: DocumentItem[]; users: User[]; onNavigate: (page: Page) => void }) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('Todos')
  const visible = documents.filter(doc => (filter === 'Todos' || doc.status === filter) && doc.title.toLowerCase().includes(query.toLowerCase()))
  return <>
    <PageHeader eyebrow="DOCUMENTOS" title="Documentos da instituição" description="Crie, acompanhe e consulte todos os documentos administrativos." action={<Button icon="plus" onClick={() => onNavigate('create')}>Novo documento</Button>}/>
    <section className="panel">
      <div className="toolbar"><label className="search"><Icon name="search" size={17}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar por título..."/></label><div className="filter-tabs">{['Todos', 'Rascunho', 'Em validação', 'Aprovado', 'Devolvido'].map(item => <button className={filter === item ? 'active' : ''} onClick={() => setFilter(item)} key={item}>{item}</button>)}</div></div>
      <div className="table-wrap"><table><thead><tr><th>Documento</th><th>Tipo</th><th>Responsável</th><th>Atualizado</th><th>Status</th></tr></thead><tbody>{visible.map(doc => <tr key={doc.id}><td><strong>{doc.title}</strong></td><td>{doc.type}</td><td>{users.find(item => item.id === doc.authorId)?.name || 'Usuário'}</td><td>{formatDate(doc.updatedAt)}</td><td><Badge status={doc.status}/></td></tr>)}</tbody></table></div>
      {!visible.length && <EmptyState title="Nenhum documento encontrado" description="Ajuste os filtros ou crie um novo documento."/>}
    </section>
  </>
}

function DocumentRow({ doc, author }: { doc: DocumentItem; author?: User }) {
  return <div className="document-row"><span className="document-row__icon"><Icon name="file"/></span><span className="document-row__main"><strong>{doc.title}</strong><small>{doc.type} · {author?.name || 'Usuário'}</small></span><span className="document-row__date">{formatDate(doc.updatedAt)}</span><Badge status={doc.status}/></div>
}

function DocumentForm({ templates, user, save }: { templates: Template[]; user: User; save: (doc: DocumentItem) => void }) {
  const [form, setForm] = useState({ title: '', type: 'Ata' as DocumentItem['type'], templateId: templates[0]?.id || '', content: '' })
  const [error, setError] = useState('')
  const submit = (status: DocumentStatus) => {
    if (!form.title.trim() || !form.content.trim()) {
      setError('Preencha o título e as informações do documento.')
      return
    }
    save({ id: crypto.randomUUID(), institutionId: user.institutionId, title: form.title.trim(), type: form.type, content: form.content.trim(), status, authorId: user.id, updatedAt: new Date().toISOString() })
  }
  return <>
    <PageHeader eyebrow="NOVO DOCUMENTO" title="Criar documento" description="Preencha as informações para gerar um novo documento administrativo."/>
    <div className="editor-grid">
      <section className="panel form-panel">
        {error && <div className="form-alert">{error}</div>}
        <Field label="Título do documento" placeholder="Ex.: Ata da reunião pedagógica — Junho" value={form.title} onChange={event => { setForm({ ...form, title: event.target.value }); setError('') }}/>
        <div className="form-grid">
          <SelectField label="Tipo de documento" value={form.type} onChange={event => setForm({ ...form, type: event.target.value as DocumentItem['type'] })}><option>Ata</option><option>Ofício</option><option>Prestação de contas</option></SelectField>
          <SelectField label="Modelo" value={form.templateId} onChange={event => setForm({ ...form, templateId: event.target.value })}><option value="">Sem modelo</option>{templates.filter(item => item.type === form.type).map(template => <option key={template.id} value={template.id}>{template.name}</option>)}</SelectField>
        </div>
        <TextArea label="Informações para o documento" value={form.content} onChange={event => { setForm({ ...form, content: event.target.value }); setError('') }} placeholder="Descreva os participantes, decisões, datas e demais informações relevantes..."/>
        <div className="form-actions"><Button variant="secondary" onClick={() => submit('Rascunho')}>Salvar rascunho</Button><Button icon="arrow" onClick={() => submit('Em validação')}>Enviar para validação</Button></div>
      </section>
      <aside className="tips-card"><span><Icon name="spark"/></span><h3>Como funciona?</h3><ol><li>Escolha o tipo e um modelo.</li><li>Insira apenas as informações necessárias.</li><li>Revise antes de enviar para validação.</li></ol><small>O conteúdo deste protótipo não é processado por IA real.</small></aside>
    </div>
  </>
}

function Templates({ templates, onUse }: { templates: Template[]; onUse: () => void }) {
  return <>
    <PageHeader eyebrow="MODELOS" title="Modelos de documentos" description="Estruturas disponíveis para padronizar a criação de documentos."/>
    <div className="card-grid">{templates.map(template => <article className="template-card" key={template.id}><span className="template-card__icon"><Icon name="layers"/></span><span className="eyebrow">{template.type}</span><h3>{template.name}</h3><p>{template.description}</p><Button variant="secondary" onClick={onUse}>Usar modelo</Button></article>)}</div>
  </>
}

function Validations({ documents, users, isAdmin, update }: { documents: DocumentItem[]; users: User[]; isAdmin: boolean; update: (id: string, status: DocumentStatus) => void }) {
  const pending = documents.filter(doc => doc.status === 'Em validação')
  return <>
    <PageHeader eyebrow="VALIDAÇÕES" title="Fila de validação" description={isAdmin ? 'Analise os documentos encaminhados pela equipe.' : 'Acompanhe os documentos enviados para análise.'}/>
    <section className="panel validation-list">
      {pending.map(doc => <div className="validation-row" key={doc.id}><span className="document-row__icon"><Icon name="file"/></span><div><strong>{doc.title}</strong><p>{doc.content}</p><small>Enviado por {users.find(item => item.id === doc.authorId)?.name} · {formatDate(doc.updatedAt)}</small></div><Badge status={doc.status}/>{isAdmin && <div className="validation-row__actions"><Button variant="secondary" onClick={() => update(doc.id, 'Devolvido')}>Devolver</Button><Button onClick={() => update(doc.id, 'Aprovado')}>Aprovar</Button></div>}</div>)}
      {!pending.length && <EmptyState icon="check" title="Tudo em dia" description="Não há documentos aguardando validação."/>}
    </section>
  </>
}

function AuditPage({ audits, users }: { audits: Audit[]; users: User[] }) {
  return <>
    <PageHeader eyebrow="AUDITORIA" title="Registro de atividades" description="Histórico rastreável das ações realizadas nesta instituição."/>
    <section className="panel"><div className="table-wrap"><table><thead><tr><th>Data e hora</th><th>Usuário</th><th>Ação</th><th>Detalhes</th></tr></thead><tbody>{audits.map(item => <tr key={item.id}><td>{formatDateTime(item.date)}</td><td><strong>{users.find(user => user.id === item.userId)?.name || 'Usuário'}</strong></td><td>{item.action}</td><td>{item.detail}</td></tr>)}</tbody></table></div>{!audits.length && <EmptyState title="Nenhuma atividade registrada" description="As ações realizadas aparecerão neste histórico."/>}</section>
  </>
}

function InstitutionPage({ institution, isAdmin, save }: { institution: Institution; isAdmin: boolean; save: (item: Institution) => void }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(institution)
  return <>
    <PageHeader eyebrow="INSTITUIÇÃO" title="Dados institucionais" description="Informações do espaço de trabalho ativo." action={isAdmin && !editing ? <Button variant="secondary" icon="edit" onClick={() => setEditing(true)}>Editar dados</Button> : undefined}/>
    <section className="panel institution-card">
      <div className="institution-card__heading"><span><Icon name="building" size={28}/></span><div><h2>{institution.name}</h2><p>{institution.type}</p></div></div>
      {editing ? <form className="form-grid" onSubmit={event => { event.preventDefault(); save(form); setEditing(false) }}>
        <div className="field--span"><Field label="Nome da instituição" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })}/></div>
        <SelectField label="Tipo" value={form.type} onChange={event => setForm({ ...form, type: event.target.value as Institution['type'] })}><option>Escola</option><option>Outra instituição</option></SelectField>
        <Field label="CNPJ" optional value={form.cnpj} onChange={event => setForm({ ...form, cnpj: event.target.value })}/>
        <Field label="E-mail institucional" type="email" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })}/>
        <Field label="Telefone" optional value={form.phone} onChange={event => setForm({ ...form, phone: event.target.value })}/>
        <div className="field--span"><Field label="Endereço" optional value={form.address} onChange={event => setForm({ ...form, address: event.target.value })}/></div>
        <div className="form-actions field--span"><Button variant="secondary" onClick={() => { setForm(institution); setEditing(false) }}>Cancelar</Button><Button type="submit">Salvar alterações</Button></div>
      </form> : <dl className="details-grid"><div><dt>CNPJ</dt><dd>{institution.cnpj || 'Não informado'}</dd></div><div><dt>E-mail institucional</dt><dd>{institution.email}</dd></div><div><dt>Telefone</dt><dd>{institution.phone || 'Não informado'}</dd></div><div><dt>Endereço</dt><dd>{institution.address || 'Não informado'}</dd></div></dl>}
      {!isAdmin && <div className="info-note"><Icon name="shield" size={18}/>Somente administradores podem editar estes dados.</div>}
    </section>
  </>
}

function UsersPage({ users, currentUser, save }: { users: User[]; currentUser: User; save: (user: User) => void }) {
  const employees = users.filter(user => user.id !== currentUser.id)
  const [modal, setModal] = useState<User | 'new' | null>(null)
  return <>
    <PageHeader eyebrow="FUNCIONÁRIOS" title="Equipe da instituição" description="Gerencie as pessoas e os perfis vinculados à instituição ativa." action={<Button icon="plus" onClick={() => setModal('new')}>Novo funcionário</Button>}/>
    <section className="panel">
      <div className="table-wrap"><table><thead><tr><th>Funcionário</th><th>Perfil</th><th>Status</th><th>Conta</th><th></th></tr></thead><tbody>{employees.map(user => <tr key={user.id}><td><div className="person-cell"><span className="avatar avatar--small">{initials(user.name)}</span><span><strong>{user.name}</strong><small>{user.email}</small></span></div></td><td>{user.role}</td><td><Badge status={user.status}/></td><td>Senha demonstrativa</td><td><button className="icon-button" onClick={() => setModal(user)} aria-label="Editar funcionário"><Icon name="edit" size={17}/></button></td></tr>)}</tbody></table></div>
      {!employees.length && <EmptyState icon="users" title="Sua equipe começa aqui" description="Cadastre o primeiro funcionário vinculado a esta instituição." action={<Button icon="plus" onClick={() => setModal('new')}>Cadastrar funcionário</Button>}/>}
    </section>
    {modal && <UserModal user={modal === 'new' ? undefined : modal} allUsers={users} institutionId={currentUser.institutionId} close={() => setModal(null)} submit={(user) => { save(user); setModal(null) }}/>}
  </>
}

function UserModal({ user, allUsers, institutionId, close, submit }: { user?: User; allUsers: User[]; institutionId: string; close: () => void; submit: (user: User) => void }) {
  const [form, setForm] = useState({ name: user?.name || '', email: user?.email || '', password: user?.password || '', role: user?.role || 'Funcionário' as Role, status: user?.status || 'Ativo' as User['status'] })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const next: Record<string, string> = {}
    if (!form.name.trim()) next.name = 'Informe o nome.'
    if (!/\S+@\S+\.\S+/.test(form.email)) next.email = 'Informe um e-mail válido.'
    if (allUsers.some(item => item.id !== user?.id && item.email.toLowerCase() === form.email.toLowerCase())) next.email = 'Este e-mail já está cadastrado nesta instituição.'
    if (form.password.length < 6) next.password = 'Use pelo menos 6 caracteres.'
    setErrors(next)
    if (Object.keys(next).length) return
    submit({ id: user?.id || crypto.randomUUID(), institutionId, ...form, name: form.name.trim(), email: form.email.trim() })
  }
  return <div className="modal-backdrop"><div className="modal"><div className="modal__header"><div><span className="eyebrow">EQUIPE</span><h2>{user ? 'Editar funcionário' : 'Novo funcionário'}</h2></div><button className="icon-button" onClick={close} aria-label="Fechar"><Icon name="close"/></button></div><p className="muted">A conta será vinculada automaticamente à instituição ativa.</p>
    <form className="form-stack" onSubmit={handleSubmit}>
      <Field label="Nome completo" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} error={errors.name}/>
      <Field label="E-mail" type="email" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })} error={errors.email}/>
      <Field label="Senha inicial demonstrativa" type="password" value={form.password} onChange={event => setForm({ ...form, password: event.target.value })} error={errors.password}/>
      <div className="form-grid"><SelectField label="Perfil de acesso" value={form.role} onChange={event => setForm({ ...form, role: event.target.value as Role })}><option>Funcionário</option><option>Administrador da instituição</option></SelectField><SelectField label="Status da conta" value={form.status} onChange={event => setForm({ ...form, status: event.target.value as User['status'] })}><option>Ativo</option><option>Inativo</option></SelectField></div>
      <div className="form-actions"><Button variant="secondary" onClick={close}>Cancelar</Button><Button type="submit">{user ? 'Salvar alterações' : 'Cadastrar funcionário'}</Button></div>
    </form>
  </div></div>
}

function EmptyState({ icon = 'file', title, description, action }: { icon?: IconName; title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state"><span><Icon name={icon}/></span><h3>{title}</h3><p>{description}</p>{action}</div>
}

function initials(name: string) {
  return name.split(' ').slice(0, 2).map(item => item[0]).join('').toUpperCase()
}
function firstName(name: string) {
  return name.split(' ')[0]
}
function shortRole(role: Role) {
  return role === 'Administrador da instituição' ? 'Administrador' : role
}
function formatDate(date: string) {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(date))
}
function formatDateTime(date: string) {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(date))
}
function relativeDate(date: string) {
  const days = Math.floor((Date.now() - new Date(date).getTime()) / 86400000)
  if (days <= 0) return 'Hoje'
  if (days === 1) return 'Ontem'
  return `Há ${days} dias`
}

export default App
