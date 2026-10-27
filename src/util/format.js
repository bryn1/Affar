// Shared display formatters (MC 11502 R3b rank 12). ONE definition of the
// timestamp format the list views render; previously byte-identical copies
// lived in Orders/Invoices/Payments, with Track using dateStyle 'medium'.
// The `dateStyle` option keeps Track's wider format without a second copy.

export function formatWhen(iso, { dateStyle = 'short' } = {}) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return new Intl.DateTimeFormat('sv-SE', { dateStyle, timeStyle: 'short' }).format(d)
}
