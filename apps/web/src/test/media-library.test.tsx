import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import App from "@/App"
import { docflowApi, getStoreSnapshot } from "@/lib/mock-api"

describe("Biblioteca de mídias — Lista, filtros, SSE/polling, pré-visualização, download e exclusão (FE-07)", () => {
  it("lista mídias, exibe status em tempo real e filtra por busca, formato e status", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )
    await user.click(screen.getByRole("button", { name: "Mídias" }))

    expect(
      screen.getByText(/Sincronizando status de processamento em tempo real/i),
    ).toBeInTheDocument()

    expect(screen.getByText("Reunião Pedagógica — Maio")).toBeInTheDocument()
    expect(
      screen.getByText("Conselho Escolar — Planejamento Semestral"),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Comissão de Prestação de Contas — Maio"),
    ).toBeInTheDocument()

    // Filtrar por formato Áudio
    await user.selectOptions(
      screen.getByLabelText(/Filtrar por formato de mídia/i),
      "Áudio",
    )
    expect(
      screen.getByText("Comissão de Prestação de Contas — Maio"),
    ).toBeInTheDocument()
    expect(
      screen.queryByText("Reunião Pedagógica — Maio"),
    ).not.toBeInTheDocument()

    // Voltar para Todos os formatos e filtrar por status Transcrito
    await user.selectOptions(
      screen.getByLabelText(/Filtrar por formato de mídia/i),
      "Todos os formatos",
    )
    await user.click(screen.getByRole("button", { name: "Transcrito" }))
    expect(screen.getByText("Reunião Pedagógica — Maio")).toBeInTheDocument()
    expect(
      screen.queryByText("Comissão de Prestação de Contas — Maio"),
    ).not.toBeInTheDocument()
  })

  it("permite pré-visualizar mídia com player e URL assinada e iniciar download (RF-07)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )
    await user.click(screen.getByRole("button", { name: "Mídias" }))

    await user.click(
      screen.getByRole("button", {
        name: /Pré-visualizar Reunião Pedagógica — Maio/i,
      }),
    )

    const dialog = screen.getByRole("dialog", {
      name: "Reunião Pedagógica — Maio",
    })
    expect(dialog).toBeInTheDocument()

    const videoPlayer = screen.getByLabelText(
      /Player de vídeo de Reunião Pedagógica — Maio/i,
    ) as HTMLVideoElement
    expect(videoPlayer.src).toContain("X-Amz-Expires=900")

    await user.click(screen.getByRole("button", { name: /Baixar original/i }))
    expect(
      screen.getByText(/Download iniciado: "reuniao-pedagogica-maio.mp4"/i),
    ).toBeInTheDocument()
  })

  it("permite cancelar e reprocessar jobs de mídia em andamento (RF-09)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )
    await user.click(screen.getByRole("button", { name: "Mídias" }))

    expect(
      screen.getByRole("progressbar", {
        name: /Progresso de Comissão de Prestação de Contas — Maio/i,
      }),
    ).toHaveAttribute("aria-valuenow", "55")

    await user.click(
      screen.getByRole("button", {
        name: /Cancelar processamento de Comissão de Prestação de Contas — Maio/i,
      }),
    )
    expect(screen.getByText("Processamento cancelado.")).toBeInTheDocument()

    await user.click(
      screen.getByRole("button", {
        name: /Reprocessar Comissão de Prestação de Contas — Maio/i,
      }),
    )
    expect(
      screen.getByText("Reprocessamento iniciado na fila."),
    ).toBeInTheDocument()

    // Avança o processamento em tempo real até concluir
    docflowApi.advanceProcessingMedia("inst-demo")
    docflowApi.advanceProcessingMedia("inst-demo")
    const completed = docflowApi.advanceProcessingMedia("inst-demo")
    expect(completed).toContain("Comissão de Prestação de Contas — Maio")
  })

  it("exclui mídia e transcrições derivadas preservando documentos aprovados (RF-07, RN-14)", async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )
    await user.click(screen.getByRole("button", { name: "Mídias" }))

    await user.click(
      screen.getByRole("button", {
        name: /Excluir Reunião Pedagógica — Maio/i,
      }),
    )

    expect(
      screen.getByRole("dialog", {
        name: /Excluir "Reunião Pedagógica — Maio"\?/i,
      }),
    ).toBeInTheDocument()

    await user.click(
      screen.getByRole("button", { name: /Confirmar exclusão/i }),
    )

    expect(
      screen.queryByText("Reunião Pedagógica — Maio"),
    ).not.toBeInTheDocument()

    const snapshot = getStoreSnapshot()
    expect(snapshot.transcripts.some((t) => t.mediaId === "media-1")).toBe(
      false,
    )
    expect(snapshot.documents.some((d) => d.status === "Aprovado")).toBe(true)
  })
})
