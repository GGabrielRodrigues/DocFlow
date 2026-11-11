export type Role = 'Administrador da instituição' | 'Funcionário'

export type Page =
  | 'dashboard'
  | 'documents'
  | 'create'
  | 'templates'
  | 'validations'
  | 'media'
  | 'transcripts'
  | 'audit'
  | 'institution'
  | 'users'

export type AuthView = 'welcome' | 'login' | 'institution' | 'first-user'

export type DocumentStatus = 'Rascunho' | 'Em validação' | 'Aprovado' | 'Devolvido'

export type MediaStatus =
  | 'Na fila'
  | 'Em processamento'
  | 'Pronto'
  | 'Transcrito'
  | 'Falhou'
  | 'Cancelado'

export type MediaKind = 'Vídeo' | 'Áudio'

export type Institution = {
  id: string
  name: string
  type: 'Escola' | 'Outra instituição'
  cnpj: string
  email: string
  phone: string
  address: string
}

/**
 * Representação segura de um usuário no cliente (`FE-01`).
 * Senhas NUNCA são armazenadas na entidade `User` nem salvas no `localStorage`.
 */
export type User = {
  id: string
  institutionId: string
  name: string
  email: string
  role: Role
  status: 'Ativo' | 'Inativo'
}

export type DocumentItem = {
  id: string
  institutionId: string
  title: string
  type: 'Ata' | 'Ofício' | 'Prestação de contas'
  content: string
  status: DocumentStatus
  authorId: string
  updatedAt: string
}

export type Template = {
  id: string
  institutionId: string
  name: string
  type: DocumentItem['type']
  description: string
}

export type Audit = {
  id: string
  institutionId: string
  userId: string
  action: string
  detail: string
  date: string
}

export type MediaItem = {
  id: string
  institutionId: string
  title: string
  fileName: string
  kind?: MediaKind
  mimeType?: string
  durationSeconds: number
  sizeBytes: number
  status: MediaStatus
  progressPercent?: number
  jobId?: string
  errorMessage?: string
  previewUrl?: string
  uploadedBy: string
  createdAt: string
}

export type TranscriptSegment = {
  id: string
  speaker: string
  startTime: string
  endTime: string
  text: string
  confidence: number
}

export type TranscriptItem = {
  id: string
  institutionId: string
  mediaId: string
  title: string
  language: 'pt-BR'
  speakersCount: number
  updatedAt: string
  segments: TranscriptSegment[]
}

export type Store = {
  institutions: Institution[]
  users: User[]
  documents: DocumentItem[]
  templates: Template[]
  audits: Audit[]
  media: MediaItem[]
  transcripts: TranscriptItem[]
}

export type CreateUserWithPasswordInput = {
  id?: string
  institutionId: string
  name: string
  email: string
  password?: string
  role: Role
  status: User['status']
}
