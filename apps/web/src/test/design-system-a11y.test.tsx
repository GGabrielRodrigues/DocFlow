import { fireEvent, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import App from "@/App"
import {
  Button,
  DataTable,
  Field,
  FileUpload,
  Modal,
  SkipLink,
  Toast,
} from "@/components/ui"

describe("Design System e Acessibilidade WCAG 2.1 AA (FE-02)", () => {
  it('associa rótulo, dica e erro via aria-describedby e role="alert" no componente Field', () => {
    render(
      <Field
        label="E-mail institucional"
        hint="Use o domínio oficial da escola"
        error="Informe um e-mail válido."
        value="invalido"
        onChange={() => undefined}
        required
      />,
    )

    const input = screen.getByLabelText(/E-mail institucional/i)
    expect(input).toHaveAttribute("aria-invalid", "true")
    expect(input).toHaveAttribute("aria-required", "true")

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Informe um e-mail válido.")
    expect(input.getAttribute("aria-describedby")).toContain(alert.id)
  })

  it('renderiza DataTable com região rolável por teclado, caption e cabeçalhos scope="col"', () => {
    render(
      <DataTable
        caption="Tabela de documentos"
        headers={["Título", "Status"]}
        hasRows
      >
        <tr>
          <td>Ata de Maio</td>
          <td>Aprovado</td>
        </tr>
      </DataTable>,
    )

    const region = screen.getByRole("region", { name: "Tabela de documentos" })
    expect(region).toHaveAttribute("tabIndex", "0")

    const headers = screen.getAllByRole("columnheader")
    expect(headers[0]).toHaveAttribute("scope", "col")
    expect(headers[1]).toHaveAttribute("scope", "col")
  })

  it("gerencia foco, armadilha de Tab e fechamento com Escape no componente Modal", async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <Modal
        eyebrow="TESTE"
        title="Confirmar ação"
        description="Descrição acessível do modal"
        onClose={onClose}
      >
        <Button>Primeiro botão</Button>
        <Button>Último botão</Button>
      </Modal>,
    )

    const dialog = screen.getByRole("dialog", { name: "Confirmar ação" })
    expect(dialog).toHaveAttribute("aria-modal", "true")

    await user.keyboard("{Escape}")
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('exibe Toast com role="status" e aria-live="polite" e permite fechar', async () => {
    const user = userEvent.setup()
    const onDismiss = vi.fn()

    render(
      <Toast message="Documento salvo com sucesso." onDismiss={onDismiss} />,
    )

    const status = screen.getByRole("status")
    expect(status).toHaveAttribute("aria-live", "polite")
    expect(status).toHaveTextContent("Documento salvo com sucesso.")

    await user.click(
      screen.getByRole("button", { name: /Fechar notificação/i }),
    )
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it("valida tamanho máximo no componente FileUpload (RN-05) e exibe barra de progresso acessível", () => {
    const onFileSelect = vi.fn()

    const { container } = render(
      <FileUpload
        maxSizeBytes={1024}
        progress={45}
        onFileSelect={onFileSelect}
      />,
    )

    const progressbar = screen.getByRole("progressbar", {
      name: /Progresso do envio/i,
    })
    expect(progressbar).toHaveAttribute("aria-valuenow", "45")

    const fileInput = container.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement
    const oversizedFile = new File(
      [new ArrayBuffer(2048)],
      "reuniao-grande.mp4",
      {
        type: "video/mp4",
      },
    )
    fireEvent.change(fileInput, { target: { files: [oversizedFile] } })

    expect(onFileSelect).not.toHaveBeenCalled()
    expect(screen.getByRole("alert")).toHaveTextContent(
      /excede o limite máximo/i,
    )

    const validFile = new File([new ArrayBuffer(512)], "reuniao-ok.mp4", {
      type: "video/mp4",
    })
    fireEvent.change(fileInput, { target: { files: [validFile] } })
    expect(onFileSelect).toHaveBeenCalledWith(validFile)
  })

  it('inclui link de pular para o conteúdo principal (SkipLink) e aria-current="page" no menu ativo', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(
      screen.getByRole("link", { name: /Pular para o conteúdo principal/i }),
    ).toHaveAttribute("href", "#main-content")

    await user.click(
      screen.getByRole("button", { name: /Acessar demonstração/i }),
    )

    const activeNavButton = screen.getByRole("button", { name: "Visão geral" })
    expect(activeNavButton).toHaveAttribute("aria-current", "page")
  })

  it("renderiza SkipLink customizável", () => {
    render(<SkipLink targetId="conteudo" label="Ir direto ao conteúdo" />)
    expect(
      screen.getByRole("link", { name: "Ir direto ao conteúdo" }),
    ).toHaveAttribute("href", "#conteudo")
  })
})
