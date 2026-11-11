import React, { ReactNode } from "react"
import { Icon, type IconName } from "./Icon"
import type { DocumentStatus, MediaStatus, User } from "@/lib/types"

export function Button({
  children,
  variant = "primary",
  icon,
  type = "button",
  onClick,
  disabled,
  className = "",
}: {
  children: ReactNode
  variant?: "primary" | "secondary" | "ghost" | "danger"
  icon?: IconName
  type?: "button" | "submit"
  onClick?: () => void
  disabled?: boolean
  className?: string
}) {
  return (
    <button
      className={`button button--${variant} ${className}`}
      type={type}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <Icon name={icon} size={17} />}
      <span>{children}</span>
    </button>
  )
}

export function Field({
  label,
  error,
  optional,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  optional?: boolean
}) {
  return (
    <label className="field">
      <span className="field__label">
        {label}
        {optional && <small>Opcional</small>}
      </span>
      <input className={error ? "input input--error" : "input"} {...props} />
      {error && <span className="field__error">{error}</span>}
    </label>
  )
}

export function SelectField({
  label,
  children,
  value,
  onChange,
  disabled,
}: {
  label: string
  children: ReactNode
  value: string
  onChange: React.ChangeEventHandler<HTMLSelectElement>
  disabled?: boolean
}) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <span className="select-wrap">
        <select
          className="input"
          value={value}
          onChange={onChange}
          disabled={disabled}
        >
          {children}
        </select>
        <Icon name="chevron" size={15} />
      </span>
    </label>
  )
}

export function TextArea({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: React.ChangeEventHandler<HTMLTextAreaElement>
  placeholder?: string
}) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <textarea
        className="input textarea"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
      />
    </label>
  )
}

export function Badge({
  status,
}: {
  status: DocumentStatus | User["status"] | MediaStatus
}) {
  const key = status
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace("ç", "c")
    .replace("ã", "a")
  return (
    <span className={`badge badge--${key}`}>
      <i />
      {status}
    </span>
  )
}

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <div className={`brand ${light ? "brand--light" : ""}`}>
      <span className="brand__mark">
        <Icon name="file" size={22} />
      </span>
      <span>
        <strong>DocFlow</strong>
        <small>Gestão administrativa</small>
      </span>
    </div>
  )
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
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

export function Stat({
  icon,
  label,
  value,
  note,
  accent = "blue",
}: {
  icon: IconName
  label: string
  value: number
  note: string
  accent?: string
}) {
  return (
    <div className="stat">
      <span className={`stat__icon stat__icon--${accent}`}>
        <Icon name={icon} />
      </span>
      <span className="stat__value">{String(value).padStart(2, "0")}</span>
      <strong>{label}</strong>
      <small>{note}</small>
    </div>
  )
}

export function EmptyState({
  icon = "file",
  title,
  description,
  action,
}: {
  icon?: IconName
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <span>
        <Icon name={icon} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  )
}
