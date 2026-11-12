import { useEffect, useMemo, useState } from "react"
import { Icon, type IconName } from "@/components/Icon"
import { Brand, SkipLink, Toast } from "@/components/ui"
import { firstName, initials, shortRole } from "@/lib/formatters"
import { onGlobalApiError } from "@/lib/http-client"
import { docflowApi } from "@/lib/mock-api"
import { useMutation, useQuery, useQueryClient } from "@/lib/query"
import { Navigate, Route, Routes, useLocation, useNavigate } from "@/lib/router"
import type {
  AuthView,
  CreateUserWithPasswordInput,
  DocumentItem,
  DocumentStatus,
  Institution,
  MediaItem,
  Page,
  Store,
} from "@/lib/types"
import { AuditPage } from "@/modules/admin/AuditPage"
import { DashboardPage } from "@/modules/admin/DashboardPage"
import { GlobalSearchModal } from "@/modules/admin/GlobalSearchModal"
import { InstitutionPage } from "@/modules/admin/InstitutionPage"
import { UsersPage } from "@/modules/admin/UsersPage"
import { AuthFlow } from "@/modules/auth/AuthFlow"
import { DocumentFormPage } from "@/modules/documents/DocumentFormPage"
import { DocumentsPage } from "@/modules/documents/DocumentsPage"
import { ValidationsPage } from "@/modules/documents/ValidationsPage"
import { MediaPage } from "@/modules/media/MediaPage"
import { TemplatesPage } from "@/modules/templates/TemplatesPage"
import { TranscriptsPage } from "@/modules/transcripts/TranscriptsPage"

interface NavItemConfig {
  id: Page
  path: string
  label: string
  icon: IconName
  adminOnly?: boolean
}

const navItems: NavItemConfig[] = [
  { id: "dashboard", path: "/", label: "Visão geral", icon: "grid" },
  { id: "documents", path: "/documents", label: "Documentos", icon: "file" },
  {
    id: "create",
    path: "/documents/new",
    label: "Novo documento",
    icon: "plus",
  },
  { id: "templates", path: "/templates", label: "Modelos", icon: "layers" },
  {
    id: "validations",
    path: "/validations",
    label: "Validações",
    icon: "check",
  },
  { id: "media", path: "/media", label: "Mídias", icon: "video" },
  {
    id: "transcripts",
    path: "/transcripts",
    label: "Transcrições",
    icon: "mic",
  },
  {
    id: "audit",
    path: "/audit",
    label: "Auditoria",
    icon: "history",
    adminOnly: true,
  },
  {
    id: "institution",
    path: "/institution",
    label: "Instituição",
    icon: "building",
  },
  {
    id: "users",
    path: "/users",
    label: "Funcionários",
    icon: "users",
    adminOnly: true,
  },
]

interface UpdateValidationInput {
  id: string
  status: DocumentStatus
}

const pageToPath: Record<Page, string> = {
  dashboard: "/",
  documents: "/documents",
  create: "/documents/new",
  templates: "/templates",
  validations: "/validations",
  media: "/media",
  transcripts: "/transcripts",
  audit: "/audit",
  institution: "/institution",
  users: "/users",
}

export function AppShell() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()

  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [authView, setAuthView] = useState<AuthView>("welcome")
  const [pendingInstitutionId, setPendingInstitutionId] =
    useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [toast, setToast] = useState("")

  const { data: store } = useQuery<Store>({
    queryKey: ["docflow-store"],
    queryFn: () => docflowApi.getStore(),
    initialData: docflowApi.getStore(),
  })

  useEffect(() => {
    return onGlobalApiError((apiError) => {
      setToast(apiError.detail || apiError.title)
    })
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(""), 3200)
    return () => window.clearTimeout(timer)
  }, [toast])

  useEffect(() => {
    if (!sidebarOpen) return
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSidebarOpen(false)
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [sidebarOpen])

  useEffect(() => {
    const handleGlobalSearchShortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setSearchOpen((prev) => !prev)
      }
    }
    document.addEventListener("keydown", handleGlobalSearchShortcut)
    return () =>
      document.removeEventListener("keydown", handleGlobalSearchShortcut)
  }, [])

  const notify = (message: string) => setToast(message)

  const refreshStore = () => {
    queryClient.setQueryData(["docflow-store"], { ...docflowApi.getStore() })
  }

  const currentUser = useMemo(
    () =>
      store.users.find(
        (user) => user.id === currentUserId && user.status === "Ativo",
      ),
    [currentUserId, store.users],
  )

  const institution = useMemo(
    () =>
      currentUser
        ? store.institutions.find(
            (item) => item.id === currentUser.institutionId,
          )
        : undefined,
    [currentUser, store.institutions],
  )

  const navigateToPage = (targetPage: Page) => {
    navigate(pageToPath[targetPage])
    setSidebarOpen(false)
  }

  const login = (email: string, password: string): boolean => {
    const user = docflowApi.authenticate(email, password)
    if (!user) return false
    refreshStore()
    setCurrentUserId(user.id)
    navigate("/")
    return true
  }

  const demoLogin = () => {
    const user = docflowApi.authenticateDemo()
    if (!user) return
    refreshStore()
    setCurrentUserId(user.id)
    navigate("/")
  }

  const logout = () => {
    docflowApi.logout(currentUser)
    refreshStore()
    setCurrentUserId(null)
    setAuthView("welcome")
    setSidebarOpen(false)
    navigate("/")
  }

  const createDocumentMutation = useMutation({
    mutationFn: (doc: DocumentItem) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.createDocument(currentUser, doc)
    },
    onSuccess: (doc) => {
      refreshStore()
      notify(
        doc.status === "Em validação"
          ? "Documento enviado para validação."
          : "Rascunho salvo com sucesso.",
      )
      navigate("/documents")
    },
  })

  const updateValidationMutation = useMutation({
    mutationFn: ({ id, status }: UpdateValidationInput) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      docflowApi.updateDocumentStatus(currentUser, id, status)
      return status
    },
    onSuccess: (status) => {
      refreshStore()
      notify(
        status === "Aprovado"
          ? "Documento aprovado."
          : "Documento devolvido ao responsável.",
      )
    },
  })

  const updateInstitutionMutation = useMutation({
    mutationFn: (updated: Institution) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.updateInstitution(currentUser, updated)
    },
    onSuccess: () => {
      refreshStore()
      notify("Dados da instituição atualizados.")
    },
  })

  const saveEmployeeMutation = useMutation({
    mutationFn: (input: CreateUserWithPasswordInput) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.saveEmployee(currentUser, input)
    },
    onSuccess: ({ existed }) => {
      refreshStore()
      notify(
        existed
          ? "Funcionário atualizado."
          : "Funcionário cadastrado com sucesso.",
      )
    },
  })

  const uploadMediaMutation = useMutation({
    mutationFn: (mediaItem: MediaItem) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.uploadMedia(currentUser, mediaItem)
    },
    onSuccess: () => {
      refreshStore()
      notify("Gravação enviada e adicionada à fila de processamento.")
    },
  })

  const deleteMediaMutation = useMutation({
    mutationFn: (mediaId: string) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.deleteMedia(currentUser, mediaId)
    },
    onSuccess: () => {
      refreshStore()
      notify("Mídia e transcrições derivadas excluídas com sucesso.")
    },
  })

  const cancelMediaJobMutation = useMutation({
    mutationFn: (mediaId: string) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.cancelMediaJob(currentUser, mediaId)
    },
    onSuccess: () => {
      refreshStore()
      notify("Processamento cancelado.")
    },
  })

  const retryMediaJobMutation = useMutation({
    mutationFn: (mediaId: string) => {
      if (!currentUser) throw new Error("Sessão inválida.")
      return docflowApi.retryMediaJob(currentUser, mediaId)
    },
    onSuccess: () => {
      refreshStore()
      notify("Reprocessamento iniciado na fila.")
    },
  })

  if (!currentUser || !institution) {
    return (
      <>
        <AuthFlow
          view={authView}
          setView={setAuthView}
          store={store}
          login={login}
          demoLogin={demoLogin}
          pendingInstitutionId={pendingInstitutionId}
          onInstitutionCreated={(newInstitution) => {
            docflowApi.createInstitution(newInstitution)
            refreshStore()
            setPendingInstitutionId(newInstitution.id)
            setAuthView("first-user")
          }}
          onAdminCreated={(adminInput) => {
            const createdAdmin = docflowApi.createFirstAdmin(adminInput)
            refreshStore()
            setCurrentUserId(createdAdmin.id)
            setPendingInstitutionId(null)
            navigate("/")
            notify("Instituição e conta criadas com sucesso.")
          }}
        />
        <Toast message={toast} onDismiss={() => setToast("")} />
      </>
    )
  }

  const scopedDocuments = store.documents.filter(
    (item) => item.institutionId === institution.id,
  )
  const scopedUsers = store.users.filter(
    (item) => item.institutionId === institution.id,
  )
  const scopedTemplates = store.templates.filter(
    (item) => item.institutionId === institution.id,
  )
  const scopedAudits = store.audits.filter(
    (item) => item.institutionId === institution.id,
  )
  const scopedMedia = store.media.filter(
    (item) => item.institutionId === institution.id,
  )
  const scopedTranscripts = store.transcripts.filter(
    (item) => item.institutionId === institution.id,
  )
  const isAdmin = currentUser.role === "Administrador da instituição"
  const pendingValidationsCount = scopedDocuments.filter(
    (doc) => doc.status === "Em validação",
  ).length

  return (
    <div className="app-shell">
      <SkipLink targetId="main-content" />
      <aside
        className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}
        aria-label="Menu lateral institucional"
      >
        <div className="sidebar__top">
          <Brand light />
          <button
            type="button"
            className="icon-button sidebar__close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Fechar menu"
          >
            <Icon name="close" />
          </button>
        </div>
        <nav className="nav" aria-label="Menu principal">
          <span className="nav__label">MENU PRINCIPAL</span>
          {navItems
            .filter((item) => !item.adminOnly || isAdmin)
            .map((item) => {
              const isActive = location.pathname === item.path
              return (
                <button
                  type="button"
                  key={item.id}
                  className={`nav__item ${isActive ? "nav__item--active" : ""}`}
                  aria-current={isActive ? "page" : undefined}
                  onClick={() => navigateToPage(item.id)}
                >
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                  {item.id === "validations" && pendingValidationsCount > 0 && (
                    <b aria-label={`${pendingValidationsCount} pendentes`}>
                      {pendingValidationsCount}
                    </b>
                  )}
                </button>
              )
            })}
        </nav>
        <div className="sidebar__notice">
          <Icon name="shield" size={18} />
          <span>
            <strong>Protótipo demonstrativo</strong>
            <small>Autenticação e dados em memória.</small>
          </span>
        </div>
        <button
          type="button"
          className="sidebar__profile"
          onClick={logout}
          aria-label={`Encerrar sessão de ${currentUser.name}`}
        >
          <span className="avatar" aria-hidden="true">
            {initials(currentUser.name)}
          </span>
          <span>
            <strong>{currentUser.name}</strong>
            <small>{shortRole(currentUser.role)}</small>
          </span>
          <Icon name="logout" size={18} />
        </button>
      </aside>
      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Fechar menu"
        />
      )}
      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="icon-button menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menu"
            aria-expanded={sidebarOpen}
          >
            <Icon name="menu" />
          </button>
          <div className="topbar__institution">
            <span className="topbar__icon" aria-hidden="true">
              <Icon name="building" size={18} />
            </span>
            <span>
              <small>INSTITUIÇÃO ATIVA</small>
              <strong>{institution.name}</strong>
            </span>
          </div>
          <div className="topbar__actions">
            <button
              type="button"
              className="topbar__search-btn"
              onClick={() => setSearchOpen(true)}
              aria-label="Abrir busca global"
            >
              <Icon name="search" size={16} />
              <span>Buscar documentos, mídias ou transcrições...</span>
              <kbd>Ctrl+K</kbd>
            </button>
            <div className="topbar__user">
              <span>
                <small>Olá,</small>
                <strong>{firstName(currentUser.name)}</strong>
              </span>
              <span className="avatar avatar--small" aria-hidden="true">
                {initials(currentUser.name)}
              </span>
            </div>
          </div>
        </header>
        <main id="main-content" className="content" tabIndex={-1}>
          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  documents={scopedDocuments}
                  media={scopedMedia}
                  users={scopedUsers}
                  audits={scopedAudits}
                  allUsers={store.users}
                  user={currentUser}
                  institution={institution}
                  onNavigate={navigateToPage}
                />
              }
            />
            <Route
              path="/documents"
              element={
                <DocumentsPage
                  documents={scopedDocuments}
                  users={store.users}
                  onNavigate={navigateToPage}
                />
              }
            />
            <Route
              path="/documents/new"
              element={
                <DocumentFormPage
                  templates={scopedTemplates}
                  user={currentUser}
                  save={(doc) => createDocumentMutation.mutate(doc)}
                />
              }
            />
            <Route
              path="/templates"
              element={
                <TemplatesPage
                  templates={scopedTemplates}
                  onUse={() => navigateToPage("create")}
                />
              }
            />
            <Route
              path="/validations"
              element={
                <ValidationsPage
                  documents={scopedDocuments}
                  users={store.users}
                  isAdmin={isAdmin}
                  update={(id, status) =>
                    updateValidationMutation.mutate({ id, status })
                  }
                />
              }
            />
            <Route
              path="/media"
              element={
                <MediaPage
                  media={scopedMedia}
                  users={store.users}
                  currentUser={currentUser}
                  onNavigate={navigateToPage}
                  onUpload={(mediaItem) =>
                    uploadMediaMutation.mutate(mediaItem)
                  }
                  onDelete={(mediaId) => deleteMediaMutation.mutate(mediaId)}
                  onCancelJob={(mediaId) =>
                    cancelMediaJobMutation.mutate(mediaId)
                  }
                  onRetryJob={(mediaId) =>
                    retryMediaJobMutation.mutate(mediaId)
                  }
                  onDownload={() => refreshStore()}
                  onRefresh={refreshStore}
                  onNotify={notify}
                />
              }
            />
            <Route
              path="/transcripts"
              element={
                <TranscriptsPage
                  transcripts={scopedTranscripts}
                  onNavigate={navigateToPage}
                />
              }
            />
            <Route
              path="/audit"
              element={
                isAdmin ? (
                  <AuditPage audits={scopedAudits} users={store.users} />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route
              path="/institution"
              element={
                <InstitutionPage
                  institution={institution}
                  isAdmin={isAdmin}
                  save={(updated) => updateInstitutionMutation.mutate(updated)}
                />
              }
            />
            <Route
              path="/users"
              element={
                isAdmin ? (
                  <UsersPage
                    users={scopedUsers}
                    currentUser={currentUser}
                    save={(userInput) => saveEmployeeMutation.mutate(userInput)}
                  />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
      {searchOpen && (
        <GlobalSearchModal
          documents={scopedDocuments}
          media={scopedMedia}
          transcripts={scopedTranscripts}
          onNavigate={navigateToPage}
          onClose={() => setSearchOpen(false)}
        />
      )}
      <Toast message={toast} onDismiss={() => setToast("")} />
    </div>
  )
}
