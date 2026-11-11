import { describe, expect, it, vi } from "vitest"
import { docflowApi, getStoreSnapshot } from "@/lib/mock-api"

describe("Segurança de dados no cliente — Sem localStorage e sem senhas armazenadas (FE-01)", () => {
  it("nunca armazena a propriedade password em objetos User da store", () => {
    const store = getStoreSnapshot()
    expect(store.users.length).toBeGreaterThan(0)

    for (const user of store.users) {
      expect("password" in user).toBe(false)
    }

    const admin = docflowApi.authenticate("marina@demo.com", "demo123")
    expect(admin).not.toBeNull()
    expect(admin && "password" in admin).toBe(false)

    const { user: createdEmployee } = docflowApi.saveEmployee(admin!, {
      institutionId: admin!.institutionId,
      name: "Carlos Pereira",
      email: "carlos@horizonte.edu.br",
      password: "senha-super-secreta",
      role: "Funcionário",
      status: "Ativo",
    })

    expect("password" in createdEmployee).toBe(false)
    expect(JSON.stringify(getStoreSnapshot())).not.toContain(
      "senha-super-secreta",
    )
    expect(JSON.stringify(getStoreSnapshot())).not.toContain("demo123")
  })

  it("não utiliza localStorage para ler ou gravar dados ou sessão", () => {
    const getItemSpy = vi.spyOn(Storage.prototype, "getItem")
    const setItemSpy = vi.spyOn(Storage.prototype, "setItem")

    const user = docflowApi.authenticateDemo()
    expect(user?.email).toBe("marina@demo.com")
    docflowApi.logout(user)

    expect(getItemSpy).not.toHaveBeenCalled()
    expect(setItemSpy).not.toHaveBeenCalled()
  })
})
