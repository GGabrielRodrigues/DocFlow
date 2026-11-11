import { setAccessToken } from './http-client'
import type {
  CreateUserWithPasswordInput,
  DocumentItem,
  DocumentStatus,
  Institution,
  MediaItem,
  Store,
  User,
} from './types'

export const DEMO_INSTITUTION = 'inst-demo'
export const DEMO_ADMIN = 'user-demo-admin'
export const DEMO_EMPLOYEE = 'user-demo-employee'

function createInitialStore(): Store {
  return {
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
        role: 'Administrador da instituição',
        status: 'Ativo',
      },
      {
        id: DEMO_EMPLOYEE,
        institutionId: DEMO_INSTITUTION,
        name: 'Rafael Nunes',
        email: 'rafael@horizonte.edu.br',
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
        authorId: DEMO_EMPLOYEE,
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
      {
        id: 'tpl-1',
        institutionId: DEMO_INSTITUTION,
        name: 'Ata de reunião',
        type: 'Ata',
        description: 'Modelo para reuniões pedagógicas e administrativas.',
      },
      {
        id: 'tpl-2',
        institutionId: DEMO_INSTITUTION,
        name: 'Ofício institucional',
        type: 'Ofício',
        description: 'Comunicação oficial com órgãos e fornecedores.',
      },
      {
        id: 'tpl-3',
        institutionId: DEMO_INSTITUTION,
        name: 'Prestação mensal',
        type: 'Prestação de contas',
        description: 'Resumo financeiro com despesas e comprovantes.',
      },
    ],
    audits: [
      {
        id: 'audit-1',
        institutionId: DEMO_INSTITUTION,
        userId: DEMO_EMPLOYEE,
        action: 'Documento encaminhado',
        detail: 'Ofício de solicitação de materiais enviado para validação',
        date: '2025-05-24T10:15:00.000Z',
      },
      {
        id: 'audit-2',
        institutionId: DEMO_INSTITUTION,
        userId: DEMO_ADMIN,
        action: 'Documento aprovado',
        detail: 'Ata da reunião pedagógica — Maio',
        date: '2025-05-22T14:30:00.000Z',
      },
    ],
    media: [
      {
        id: 'media-1',
        institutionId: DEMO_INSTITUTION,
        title: 'Reunião Pedagógica — Maio',
        fileName: 'reuniao-pedagogica-maio.mp4',
        durationSeconds: 3420,
        sizeBytes: 420 * 1024 * 1024,
        status: 'Transcrito',
        uploadedBy: DEMO_ADMIN,
        createdAt: '2025-05-22T13:00:00.000Z',
      },
      {
        id: 'media-2',
        institutionId: DEMO_INSTITUTION,
        title: 'Conselho Escolar — Planejamento Semestral',
        fileName: 'conselho-escolar-semestral.mp4',
        durationSeconds: 2715,
        sizeBytes: 310 * 1024 * 1024,
        status: 'Pronto',
        uploadedBy: DEMO_EMPLOYEE,
        createdAt: '2025-05-24T09:10:00.000Z',
      },
    ],
    transcripts: [
      {
        id: 'tr-1',
        institutionId: DEMO_INSTITUTION,
        mediaId: 'media-1',
        title: 'Transcrição — Reunião Pedagógica — Maio',
        language: 'pt-BR',
        speakersCount: 2,
        updatedAt: '2025-05-22T14:00:00.000Z',
        segments: [
          {
            id: 'seg-1',
            speaker: 'Marina Carvalho',
            startTime: '00:00:12',
            endTime: '00:00:28',
            text: 'Bom dia a todos. Vamos iniciar a pauta pedagógica do mês de maio revisando o calendário.',
            confidence: 0.98,
          },
          {
            id: 'seg-2',
            speaker: 'Rafael Nunes',
            startTime: '00:00:29',
            endTime: '00:00:46',
            text: 'Os materiais didáticos do segundo semestre já foram levantados junto aos professores.',
            confidence: 0.95,
          },
        ],
      },
    ],
  }
}

let memoryStore: Store = createInitialStore()

/**
 * Verificador efêmero de credenciais de demonstração em memória.
 * Senhas nunca fazem parte da entidade `User` nem são persistidas em `localStorage`.
 */
const demoCredentialMap = new Map<string, string>([
  [DEMO_ADMIN, 'demo123'],
  [DEMO_EMPLOYEE, 'demo123'],
])

export function resetMemoryStore(): void {
  memoryStore = createInitialStore()
  demoCredentialMap.clear()
  demoCredentialMap.set(DEMO_ADMIN, 'demo123')
  demoCredentialMap.set(DEMO_EMPLOYEE, 'demo123')
  setAccessToken(null)
}

export function getStoreSnapshot(): Store {
  return memoryStore
}

function recordAudit(user: User, action: string, detail: string): void {
  memoryStore = {
    ...memoryStore,
    audits: [
      {
        id: crypto.randomUUID(),
        institutionId: user.institutionId,
        userId: user.id,
        action,
        detail,
        date: new Date().toISOString(),
      },
      ...memoryStore.audits,
    ],
  }
}

export const docflowApi = {
  getStore(): Store {
    return memoryStore
  },

  authenticate(email: string, password: string): User | null {
    const normalizedEmail = email.trim().toLowerCase()
    const user = memoryStore.users.find(
      (item) => item.email.toLowerCase() === normalizedEmail && item.status === 'Ativo',
    )
    if (!user) return null
    const expectedPassword = demoCredentialMap.get(user.id)
    if (!expectedPassword || expectedPassword !== password) return null

    setAccessToken(`demo-jwt-${user.id}`)
    recordAudit(user, 'Acesso realizado', 'Usuário entrou na aplicação')
    return user
  },

  authenticateDemo(): User | null {
    const demoUser = memoryStore.users.find(
      (user) => user.id === DEMO_ADMIN && user.status === 'Ativo',
    )
    if (!demoUser) return null
    setAccessToken(`demo-jwt-${demoUser.id}`)
    recordAudit(demoUser, 'Acesso demonstrativo', 'Sessão de demonstração iniciada')
    return demoUser
  },

  logout(currentUser: User | null | undefined): void {
    if (currentUser) {
      recordAudit(currentUser, 'Sessão encerrada', 'Usuário saiu da aplicação')
    }
    setAccessToken(null)
  },

  createInstitution(newInstitution: Institution): Institution {
    memoryStore = {
      ...memoryStore,
      institutions: [...memoryStore.institutions, newInstitution],
    }
    return newInstitution
  },

  createFirstAdmin(input: CreateUserWithPasswordInput): User {
    const user: User = {
      id: input.id || crypto.randomUUID(),
      institutionId: input.institutionId,
      name: input.name.trim(),
      email: input.email.trim(),
      role: input.role,
      status: input.status,
    }
    if (input.password) {
      demoCredentialMap.set(user.id, input.password)
    }

    memoryStore = {
      ...memoryStore,
      users: [...memoryStore.users, user],
      templates: [
        ...memoryStore.templates,
        {
          id: crypto.randomUUID(),
          institutionId: user.institutionId,
          name: 'Ata de reunião',
          type: 'Ata',
          description: 'Modelo base para reuniões administrativas.',
        },
        {
          id: crypto.randomUUID(),
          institutionId: user.institutionId,
          name: 'Ofício institucional',
          type: 'Ofício',
          description: 'Modelo para comunicações oficiais.',
        },
      ],
      audits: [
        {
          id: crypto.randomUUID(),
          institutionId: user.institutionId,
          userId: user.id,
          action: 'Conta criada',
          detail: 'Primeiro administrador da instituição cadastrado',
          date: new Date().toISOString(),
        },
        ...memoryStore.audits,
      ],
    }
    setAccessToken(`demo-jwt-${user.id}`)
    return user
  },

  createDocument(currentUser: User, doc: DocumentItem): DocumentItem {
    memoryStore = {
      ...memoryStore,
      documents: [doc, ...memoryStore.documents],
      audits: [
        {
          id: crypto.randomUUID(),
          institutionId: currentUser.institutionId,
          userId: currentUser.id,
          action: doc.status === 'Em validação' ? 'Documento encaminhado' : 'Documento criado',
          detail: doc.title,
          date: new Date().toISOString(),
        },
        ...memoryStore.audits,
      ],
    }
    return doc
  },

  updateDocumentStatus(currentUser: User, id: string, status: DocumentStatus): void {
    const doc = memoryStore.documents.find((item) => item.id === id)
    memoryStore = {
      ...memoryStore,
      documents: memoryStore.documents.map((item) =>
        item.id === id ? { ...item, status, updatedAt: new Date().toISOString() } : item,
      ),
      audits: [
        {
          id: crypto.randomUUID(),
          institutionId: currentUser.institutionId,
          userId: currentUser.id,
          action: status === 'Aprovado' ? 'Documento aprovado' : 'Documento devolvido',
          detail: doc?.title || 'Documento',
          date: new Date().toISOString(),
        },
        ...memoryStore.audits,
      ],
    }
  },

  updateInstitution(currentUser: User, updated: Institution): Institution {
    memoryStore = {
      ...memoryStore,
      institutions: memoryStore.institutions.map((item) =>
        item.id === updated.id ? updated : item,
      ),
    }
    recordAudit(currentUser, 'Instituição atualizada', 'Dados básicos da instituição foram alterados')
    return updated
  },

  saveEmployee(
    currentUser: User,
    input: CreateUserWithPasswordInput,
  ): { user: User; existed: boolean } {
    const userId = input.id || crypto.randomUUID()
    const exists = memoryStore.users.some((item) => item.id === userId)
    const user: User = {
      id: userId,
      institutionId: input.institutionId,
      name: input.name.trim(),
      email: input.email.trim(),
      role: input.role,
      status: input.status,
    }
    if (input.password) {
      demoCredentialMap.set(user.id, input.password)
    } else if (!demoCredentialMap.has(user.id)) {
      demoCredentialMap.set(user.id, 'demo123')
    }

    memoryStore = {
      ...memoryStore,
      users: exists
        ? memoryStore.users.map((item) => (item.id === user.id ? user : item))
        : [...memoryStore.users, user],
    }
    recordAudit(
      currentUser,
      exists ? 'Funcionário atualizado' : 'Funcionário cadastrado',
      user.name,
    )
    return { user, existed: exists }
  },

  uploadMedia(currentUser: User, mediaItem: MediaItem): MediaItem {
    memoryStore = {
      ...memoryStore,
      media: [mediaItem, ...memoryStore.media],
    }
    recordAudit(currentUser, 'Mídia enviada', mediaItem.title)
    return mediaItem
  },
}
