import { EmptyState, PageHeader } from "@/components/ui"
import { formatDateTime } from "@/lib/formatters"
import type { Audit, User } from "@/lib/types"

export function AuditPage({
  audits,
  users,
}: {
  audits: Audit[]
  users: User[]
}) {
  return (
    <>
      <PageHeader
        eyebrow="AUDITORIA"
        title="Registro de atividades"
        description="Histórico rastreável das ações realizadas nesta instituição."
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Data e hora</th>
                <th>Usuário</th>
                <th>Ação</th>
                <th>Detalhes</th>
              </tr>
            </thead>
            <tbody>
              {audits.map((item) => (
                <tr key={item.id}>
                  <td>{formatDateTime(item.date)}</td>
                  <td>
                    <strong>
                      {users.find((user) => user.id === item.userId)?.name ||
                        "Usuário"}
                    </strong>
                  </td>
                  <td>{item.action}</td>
                  <td>{item.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!audits.length && (
          <EmptyState
            title="Nenhuma atividade registrada"
            description="As ações realizadas aparecerão neste histórico."
          />
        )}
      </section>
    </>
  )
}
