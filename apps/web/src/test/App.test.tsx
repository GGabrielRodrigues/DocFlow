import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import App from "@/App"

describe("Integração de módulos e rotas do Frontend (FE-01)", () => {
  it("permite acessar a demonstração como Administrador e navegar entre os módulos", async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getByText("Como deseja começar?")).toBeInTheDocument()

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )

    expect(screen.getByText(/Bom dia, Marina\./i)).toBeInTheDocument()
    expect(screen.getByText("Escola Municipal Horizonte")).toBeInTheDocument()

    // Navegar para Mídias
    await user.click(screen.getByRole("button", { name: "Mídias" }))
    expect(screen.getByText("Gravações da instituição")).toBeInTheDocument()
    expect(screen.getByText("Reunião Pedagógica — Maio")).toBeInTheDocument()

    // Navegar para Transcrições
    await user.click(screen.getByRole("button", { name: "Transcrições" }))
    expect(screen.getByText("Transcrições com diarização")).toBeInTheDocument()

    // Navegar para Funcionários (visível para Administrador)
    await user.click(screen.getByRole("button", { name: "Funcionários" }))
    expect(screen.getByText("Equipe da instituição")).toBeInTheDocument()
    expect(screen.getByText("Rafael Nunes")).toBeInTheDocument()
  })

  it("oculta gestão de funcionários quando autenticado como Funcionário (RBAC)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Entrar na minha conta/i }),
    )
    await user.type(screen.getByLabelText(/E-mail/i), "rafael@horizonte.edu.br")
    await user.type(screen.getByLabelText(/Senha/i), "demo123")
    await user.click(screen.getByRole("button", { name: /^Entrar$/i }))

    expect(screen.getByText(/Bom dia, Rafael\./i)).toBeInTheDocument()
    expect(
      screen.queryByRole("button", { name: "Funcionários" }),
    ).not.toBeInTheDocument()
  })
})
