import { Component, ErrorInfo, ReactNode } from "react"
import { Button } from "./ui"

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    message: "",
  }

  static getDerivedStateFromError(error: unknown): ErrorBoundaryState {
    const message =
      error instanceof Error
        ? error.message
        : "Ocorreu um erro inesperado ao renderizar a aplicação."
    return { hasError: true, message }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("Erro capturado pelo ErrorBoundary global:", error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, message: "" })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="auth__panel" role="alert">
          <div className="auth-card panel form-panel">
            <span className="eyebrow">ERRO INESPERADO</span>
            <h2>Algo não saiu como esperado</h2>
            <p className="muted">{this.state.message}</p>
            <div className="form-actions">
              <Button onClick={this.handleReset}>Tentar novamente</Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
