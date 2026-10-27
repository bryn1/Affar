import * as api from '../api.js'
import { useAuth } from '../auth.context.jsx'
import { useResource } from '../useResource.js'
import { formatWhen } from '../util/format.js'
import DataTable from '../components/DataTable.jsx'
import Money from '../components/Money.jsx'

// Payments (C17) — read-only ledger of recorded payments. Amount is a
// Decimal(12,2) owned by the server; this view only formats it.
export default function Payments() {
  const { token } = useAuth()
  const { rows, loading, error } = useResource(() => api.listPayments(token), [token])

  const columns = [
    { key: 'id', label: 'Nr', render: (r) => <span className="mono">#{r.id}</span> },
    {
      key: 'invoice_id', label: 'Faktura', render: (r) =>
        r.invoice_id != null ? <span className="mono">#{r.invoice_id}</span> : <span className="muted">—</span>,
    },
    { key: 'method', label: 'Metod', render: (r) => (r.method || '—') },
    { key: 'amount', label: 'Belopp', align: 'num', render: (r) => <Money value={r.amount} /> },
    { key: 'date', label: 'Datum', render: (r) => formatWhen(r.paid_at) },
  ]

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h2>Betalningar</h2>
          <p>Registrerade inbetalningar.</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        error={error}
        emptyText="Inga betalningar registrerade ännu."
        ariaLabel="Betalningslista"
        keyOf={(r) => r.id}
      />
    </div>
  )
}
