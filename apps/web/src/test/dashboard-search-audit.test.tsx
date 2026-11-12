import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import App from "@/App"

describe("Dashboard, busca global e auditoria (FE-15 — RF-27, RF-28, RF-29)", () => {
  it("exibe o dashboard institucional real com distribuição por status e fila de mídia em processamento (RF-28)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )

    expect(
      screen.getByRole("heading", { name: /Bom dia, Marina\./i }),
    ).toBeInTheDocument()

    // Distribuição por status (RF-28)
    const breakdownGroup = screen.getByRole("group", {
      name: "Documentos por status",
    })
    expect(within(breakdownGroup).getByText("Aprovado")).toBeInTheDocument()
    expect(within(breakdownGroup).getByText("Em validação")).toBeInTheDocument()
    expect(within(breakdownGroup).getByText("Rascunho")).toBeInTheDocument()
    expect(within(breakdownGroup).getByText("Devolvido")).toBeInTheDocument()

    // Mídias em processamento (RF-28)
    expect(
      screen.getByRole("heading", { name: "Mídias em processamento" }),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Comissão de Prestação de Contas — Maio"),
    ).toBeInTheDocument()
  })

  it("permite realizar busca global entre documentos, mídias e transcrições e filtrar localmente (RF-29)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )

    // Abre modal de busca global
    await user.click(
      screen.getByRole("button", { name: /Abrir busca global/i }),
    )

    const dialog = screen.getByRole("dialog", {
      name: "Pesquisar na instituição",
    })
    expect(dialog).toBeInTheDocument()

    const searchInput = within(dialog).getByLabelText("Termo de busca global")
    await user.type(searchInput, "pedagógica")

    // Deve encontrar documento, mídia e transcrição relacionados a pedagógica
    expect(
      within(dialog).getByText("Ata da reunião pedagógica — Maio"),
    ).toBeInTheDocument()
    expect(
      within(dialog).getByText("Reunião Pedagógica — Maio"),
    ).toBeInTheDocument()
    expect(
      within(dialog).getByText("Transcrição — Reunião Pedagógica — Maio"),
    ).toBeInTheDocument()

    // Filtra apenas por escopo Transcrições no modal
    const scopeGroup = within(dialog).getByRole("group", {
      name: "Filtrar resultados da busca global",
    })
    await user.click(
      within(scopeGroup).getByRole("button", { name: "Transcrições" }),
    )
    const transcriptResult = within(dialog).getByRole("button", {
      name: /Transcrição — Reunião Pedagógica — Maio/i,
    })
    expect(transcriptResult).toBeInTheDocument()

    // Clicar no resultado navega para a página de transcrições e fecha o modal
    await user.click(transcriptResult)
    expect(
      screen.getByRole("heading", { name: "Transcrições com diarização" }),
    ).toBeInTheDocument()

    // Testa busca local na tela de Transcrições (RF-29)
    const transcriptSearch = screen.getByLabelText(
      "Buscar em transcrições por título, falante ou trecho",
    )
    await user.type(transcriptSearch, "calendário")
    expect(
      screen.getByText("Transcrição — Reunião Pedagógica — Maio"),
    ).toBeInTheDocument()

    // Testa filtro por tipo na tela de Documentos (RF-29)
    await user.click(screen.getByRole("button", { name: "Documentos" }))
    await user.selectOptions(
      screen.getByLabelText("Filtrar documentos por tipo"),
      "Ofício",
    )
    expect(
      screen.getByText("Ofício de solicitação de materiais"),
    ).toBeInTheDocument()
    expect(
      screen.queryByText("Ata da reunião pedagógica — Maio"),
    ).not.toBeInTheDocument()
  })

  it("permite ao administrador filtrar a trilha de auditoria por texto, usuário, categoria e período (RF-27, RN-11)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )
    await user.click(screen.getByRole("button", { name: "Auditoria" }))

    expect(
      screen.getByRole("heading", { name: "Registro de atividades" }),
    ).toBeInTheDocument()
    expect(screen.getByText(/Trilha imutável \(RN-11\)/i)).toBeInTheDocument()

    // Filtrar por categoria Autenticação
    await user.selectOptions(
      screen.getByLabelText("Filtrar auditoria por categoria"),
      "Autenticação",
    )
    expect(screen.getByText("Acesso demonstrativo")).toBeInTheDocument()
    expect(screen.queryByText("Documento aprovado")).not.toBeInTheDocument()

    // Voltar para Todas as categorias e filtrar por usuário Rafael Nunes (user-demo-employee)
    await user.selectOptions(
      screen.getByLabelText("Filtrar auditoria por categoria"),
      "Todas as categorias",
    )
    await user.selectOptions(
      screen.getByLabelText("Filtrar auditoria por usuário"),
      "user-demo-employee",
    )
    expect(screen.getByText("Documento encaminhado")).toBeInTheDocument()
    expect(screen.queryByText("Documento aprovado")).not.toBeInTheDocument()
  })

  it("restringe o acesso à tela de auditoria apenas ao Administrador da instituição (RF-27, RN-03)", async () => {
    const user = userEvent.setup()
    render(<App />)

    // Faz login como Funcionário (Rafael Nunes)
    await user.click(
      screen.getByRole("button", { name: /Entrar na minha conta/i }),
    )
    await user.type(screen.getByLabelText(/E-mail/i), "rafael@horizonte.edu.br")
    await user.type(screen.getByLabelText(/Senha/i), "demo123")
    await user.click(screen.getByRole("button", { name: /^Entrar$/i }))

    expect(
      screen.getByRole("heading", { name: /Bom dia, Rafael\./i }),
    ).toBeInTheDocument()

    // Funcionário não deve ver o item Auditoria no menu lateral
    expect(
      screen.queryByRole("button", { name: "Auditoria" }),
    ).not.toBeInTheDocument()
  })
})
