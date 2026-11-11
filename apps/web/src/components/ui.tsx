import React, { ReactNode, useEffect, useId, useRef, useState } from "react"
import { Icon, type IconName } from "./Icon"
import { formatFileSize } from "@/lib/formatters"
import type { DocumentStatus, MediaStatus, User } from "@/lib/types"

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024 * 1024 // 10 GB (RN-05)

export interface SkipLinkProps {
  targetId?: string
  label?: string
}

export function SkipLink({
  targetId = "main-content",
  label = "Pular para o conteúdo principal",
}: SkipLinkProps) {
  return (
    <a className="skip-link" href={`#${targetId}`}>
      {label}
    </a>
  )
}

export interface ButtonProps {
  children: ReactNode
  variant?: "primary" | "secondary" | "ghost" | "danger"
  icon?: IconName
  type?: "button" | "submit"
  onClick?: () => void
  disabled?: boolean
  loading?: boolean
  className?: string
  ariaLabel?: string
}

export function Button({
  children,
  variant = "primary",
  icon,
  type = "button",
  onClick,
  disabled,
  loading = false,
  className = "",
  ariaLabel,
}: ButtonProps) {
  return (
    <button
      className={`button button--${variant} ${className}`.trim()}
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      aria-label={ariaLabel}
    >
      {icon && <Icon name={icon} size={17} />}
      <span>{children}</span>
    </button>
  )
}

export interface FieldProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
  optional?: boolean
}

export function Field({
  label,
  error,
  hint,
  optional,
  id: providedId,
  required,
  ...props
}: FieldProps) {
  const generatedId = useId()
  const inputId = providedId || `field-${generatedId}`
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`
  const describedBy = [hint ? hintId : null, error ? errorId : null]
    .filter(Boolean)
    .join(" ")

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        <span>{label}</span>
        {optional && <small>Opcional</small>}
      </label>
      <input
        id={inputId}
        className={error ? "input input--error" : "input"}
        required={required}
        aria-required={required || undefined}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy || undefined}
        {...props}
      />
      {hint && (
        <span id={hintId} className="field__hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}

export interface SelectFieldProps {
  label: string
  children: ReactNode
  value: string
  onChange: React.ChangeEventHandler<HTMLSelectElement>
  disabled?: boolean
  error?: string
  id?: string
}

export function SelectField({
  label,
  children,
  value,
  onChange,
  disabled,
  error,
  id: providedId,
}: SelectFieldProps) {
  const generatedId = useId()
  const selectId = providedId || `select-${generatedId}`
  const errorId = `${selectId}-error`

  return (
    <div className="field">
      <label className="field__label" htmlFor={selectId}>
        <span>{label}</span>
      </label>
      <span className="select-wrap">
        <select
          id={selectId}
          className={error ? "input input--error" : "input"}
          value={value}
          onChange={onChange}
          disabled={disabled}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
        >
          {children}
        </select>
        <Icon name="chevron" size={15} />
      </span>
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}

export interface TextAreaProps {
  label: string
  value: string
  onChange: React.ChangeEventHandler<HTMLTextAreaElement>
  placeholder?: string
  error?: string
  id?: string
}

export function TextArea({
  label,
  value,
  onChange,
  placeholder,
  error,
  id: providedId,
}: TextAreaProps) {
  const generatedId = useId()
  const textareaId = providedId || `textarea-${generatedId}`
  const errorId = `${textareaId}-error`

  return (
    <div className="field">
      <label className="field__label" htmlFor={textareaId}>
        <span>{label}</span>
      </label>
      <textarea
        id={textareaId}
        className={error ? "input textarea input--error" : "input textarea"}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      />
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}

export interface BadgeProps {
  status: DocumentStatus | User["status"] | MediaStatus
}

export function Badge({ status }: BadgeProps) {
  const key = status
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace("ç", "c")
    .replace("ã", "a")
  return (
    <span className={`badge badge--${key}`}>
      <i aria-hidden="true" />
      {status}
    </span>
  )
}

export interface BrandProps {
  light?: boolean
}

export function Brand({ light = false }: BrandProps) {
  return (
    <div className={`brand ${light ? "brand--light" : ""}`}>
      <span className="brand__mark" aria-hidden="true">
        <Icon name="file" size={22} />
      </span>
      <span>
        <strong>DocFlow</strong>
        <small>Gestão administrativa</small>
      </span>
    </div>
  )
}

export interface PageHeaderProps {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  )
}

export interface StatProps {
  icon: IconName
  label: string
  value: number
  note: string
  accent?: string
}

export function Stat({ icon, label, value, note, accent = "blue" }: StatProps) {
  return (
    <div className="stat" role="group" aria-label={`${label}: ${value}`}>
      <span className={`stat__icon stat__icon--${accent}`} aria-hidden="true">
        <Icon name={icon} />
      </span>
      <span className="stat__value">{String(value).padStart(2, "0")}</span>
      <strong>{label}</strong>
      <small>{note}</small>
    </div>
  )
}

export interface EmptyStateProps {
  icon?: IconName
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({
  icon = "file",
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="empty-state" role="status">
      <span aria-hidden="true">
        <Icon name={icon} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  )
}

export interface DataTableProps {
  caption: string
  headers: string[]
  children: ReactNode
  emptyState?: ReactNode
  hasRows?: boolean
}

export function DataTable({
  caption,
  headers,
  children,
  emptyState,
  hasRows = true,
}: DataTableProps) {
  return (
    <>
      <div
        className="table-wrap"
        role="region"
        aria-label={caption}
        tabIndex={0}
      >
        <table>
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {headers.map((header, index) => (
                <th key={`${header || "actions"}-${index}`} scope="col">
                  {header || <span className="sr-only">Ações</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>{children}</tbody>
        </table>
      </div>
      {!hasRows && emptyState}
    </>
  )
}

export interface ModalProps {
  eyebrow?: string
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
}

export function Modal({
  eyebrow,
  title,
  description,
  onClose,
  children,
}: ModalProps) {
  const titleId = useId()
  const descriptionId = useId()
  const modalRef = useRef<HTMLDivElement | null>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    const previousFocused = document.activeElement as HTMLElement | null
    const container = modalRef.current
    if (container) {
      const firstInput = container.querySelector<HTMLElement>(
        "input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])",
      )
      ;(firstInput || container).focus()
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault()
        onCloseRef.current()
        return
      }
      if (event.key === "Tab" && modalRef.current) {
        const focusable = Array.from(
          modalRef.current.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        )
        if (focusable.length === 0) return
        const first = focusable[0]!
        const last = focusable[focusable.length - 1]!
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
      previousFocused?.focus?.()
    }
  }, [])

  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        ref={modalRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
      >
        <div className="modal__header">
          <div>
            {eyebrow && <span className="eyebrow">{eyebrow}</span>}
            <h2 id={titleId}>{title}</h2>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Fechar janela"
          >
            <Icon name="close" />
          </button>
        </div>
        {description && (
          <p id={descriptionId} className="muted">
            {description}
          </p>
        )}
        {children}
      </div>
    </div>
  )
}

export interface ToastProps {
  message: string
  onDismiss?: () => void
}

export function Toast({ message, onDismiss }: ToastProps) {
  if (!message) return null
  return (
    <div className="toast" role="status" aria-live="polite" aria-atomic="true">
      <span aria-hidden="true">
        <Icon name="check" size={16} />
      </span>
      <p className="toast__text">{message}</p>
      {onDismiss && (
        <button
          type="button"
          className="toast__close"
          onClick={onDismiss}
          aria-label="Fechar notificação"
        >
          <Icon name="close" size={14} />
        </button>
      )}
    </div>
  )
}

export interface FileUploadProps {
  label?: string
  description?: string
  accept?: string
  maxSizeBytes?: number
  progress?: number | null
  onFileSelect: (file: File) => void
}

export function FileUpload({
  label = "Selecionar ou arrastar arquivo de mídia",
  description = "Formatos aceitos: MP4, MKV, MOV, WEBM, MP3, WAV ou M4A · Limite máximo: 10 GB / 2h30 (RN-05)",
  accept = ".mp4,.mkv,.mov,.webm,.mp3,.wav,.m4a,video/*,audio/*",
  maxSizeBytes = MAX_UPLOAD_SIZE_BYTES,
  progress = null,
  onFileSelect,
}: FileUploadProps) {
  const inputId = useId()
  const descriptionId = `${inputId}-desc`
  const errorId = `${inputId}-error`
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState("")

  const handleFile = (file: File | undefined) => {
    if (!file) return
    if (file.size > maxSizeBytes) {
      setError(
        `O arquivo "${file.name}" (${formatFileSize(file.size)}) excede o limite máximo de ${formatFileSize(maxSizeBytes)} (RN-05).`,
      )
      setSelectedFile(null)
      return
    }
    setError("")
    setSelectedFile(file)
    onFileSelect(file)
  }

  return (
    <div className="upload-field">
      <div
        className={`upload-dropzone ${
          dragging ? "upload-dropzone--active" : ""
        } ${error ? "upload-dropzone--error" : ""}`.trim()}
        role="button"
        tabIndex={0}
        aria-label={label}
        aria-describedby={error ? `${descriptionId} ${errorId}` : descriptionId}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          handleFile(event.dataTransfer.files?.[0])
        }}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="sr-only"
          accept={accept}
          onChange={(event) => handleFile(event.target.files?.[0])}
        />
        <span className="upload-dropzone__icon" aria-hidden="true">
          <Icon name="upload" size={22} />
        </span>
        <strong>{label}</strong>
        <small id={descriptionId}>{description}</small>
        {selectedFile && (
          <span className="upload-dropzone__file" role="status">
            Arquivo selecionado: <strong>{selectedFile.name}</strong> (
            {formatFileSize(selectedFile.size)})
          </span>
        )}
      </div>
      {typeof progress === "number" && (
        <div
          className="upload-progress"
          role="progressbar"
          aria-label="Progresso do envio"
          aria-valuenow={Math.min(100, Math.max(0, Math.round(progress)))}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="upload-progress__bar"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
