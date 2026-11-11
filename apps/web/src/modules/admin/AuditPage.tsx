import { DataTable, EmptyState, PageHeader } from "@/components/ui"
import { formatDateTime } from "@/lib/formatters"
import type { Audit, User } from "@/lib/types"

export interface AuditPageProps {
  audits: Audit[]
  users: User[]
}

export function AuditPage({ audits, users }: AuditPageProps) {
  return (
    <>
      <PageHeader
        eyebrow="AUDITORIA"
        title="Registro de atividades"
        description="Histórico rastreável das ações realizadas nesta instituição."
      />
      <section className="panel">
        <DataTable
          caption="Histórico de auditoria da instituição"
          headers={["Data e hora", "Usuário", "Ação", "Detalhes"]}
          hasRows={audits.length > 0}
          emptyState={
            <EmptyState
              title="Nenhuma atividade registrada"
              description="As ações realizadas aparecerão neste histórico."
            />
          }
        >
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
        </DataTable>
      </section>
    </>
  )
}
