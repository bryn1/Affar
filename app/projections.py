"""Shared wire projections (MC 11499 rank 9).

A projection belongs here when more than one router needs it: routers/payments
imported the private ``_invoice_to_out`` out of routers/invoices (the audit's
rank 9). The invoice projection — C16 InvoiceOut with server-owned Decimal
money and UTC ISO timestamps — now lives here as a public function and both
routers import it. Routers keep only their own single-router projections.
"""

from datetime import UTC
from decimal import Decimal

from app.models import Invoice
from app.schemas.invoice import InvoiceOut


def invoice_to_out(invoice: Invoice) -> InvoiceOut:
    """Project an ORM Invoice (with loaded lines + payments) onto the wire set.

    total is the server-stored Decimal; timestamps converted to UTC ISO.
    """
    return InvoiceOut(
        id=invoice.id,
        order_id=invoice.order_id,
        invoice_no=invoice.invoice_no,
        status=invoice.status,
        total=Decimal(invoice.total).quantize(Decimal("0.01")),
        issued_at=(
            invoice.issued_at.astimezone(UTC).isoformat()
            if invoice.issued_at else None
        ),
        paid_at=(
            invoice.paid_at.astimezone(UTC).isoformat()
            if invoice.paid_at else None
        ),
        lines=[
            {
                "id": ln.id,
                "item_id": ln.item_id,
                "description": ln.description,
                "qty": ln.qty,
                "unit_price": Decimal(ln.unit_price).quantize(Decimal("0.01")),
                "line_total": Decimal(ln.line_total).quantize(Decimal("0.01")),
            }
            for ln in invoice.lines
        ],
        payments=[
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "amount": Decimal(p.amount).quantize(Decimal("0.01")),
                "method": p.method,
                "paid_at": p.paid_at.astimezone(UTC).isoformat(),
            }
            for p in invoice.payments
        ],
    )
