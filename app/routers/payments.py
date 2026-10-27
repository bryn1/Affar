"""Payments router (contract C17) — HTTP surface for payments.

    POST   /api/invoices/{id}/payment   PaymentIn -> PaymentOut  [admin, finance]
    POST   /api/invoices/{id}/reconcile -> InvoiceOut            [admin, finance]
    GET    /api/payments                -> list[PaymentOut]
    POST   /api/payments/{id}/cancel    -> PaymentOut            [admin, finance]

Recording is simulated (I3) — no gateway. The amount is validated in the schema
(gt=0, 12,2) so the service always sees a Decimal. Reconcile reuses the invoice
projection so the response shape matches C16's InvoiceOut — the projection is
shared via app.projections (MC 11499 rank 9), never a router-private import.
MC 1175.3: /payments/{id}/cancel is makulering — an append-only negative
refund row linked back via cancels_payment_id (never a delete).
MC 11499 rank 8: the cancelled-invoice money gate lives in the service
(services.payments.record_payment, 410), not on this router.
"""

from datetime import UTC
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import roles
from app.auth import require_role
from app.database import get_session
from app.projections import invoice_to_out
from app.schemas.payment import PaymentIn, PaymentOut
from app.schemas.invoice import InvoiceOut

from app.services import payments as svc

router = APIRouter(prefix="/api", tags=["payments"])


def _payment_to_out(payment) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=Decimal(payment.amount).quantize(Decimal("0.01")),
        method=payment.method,
        paid_at=payment.paid_at.astimezone(UTC).isoformat(),
        cancels_payment_id=payment.cancels_payment_id,
    )


@router.post("/invoices/{invoice_id}/payment", response_model=PaymentOut)
def create_payment(
    invoice_id: int,
    body: PaymentIn,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> PaymentOut:
    payment = svc.record_payment(
        db, invoice_id, body.amount, body.method, body.date
    )
    return _payment_to_out(payment)


@router.post("/invoices/{invoice_id}/reconcile", response_model=InvoiceOut)
def reconcile(
    invoice_id: int,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
):
    invoice = svc.reconcile(db, invoice_id)
    return invoice_to_out(invoice)


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> list[PaymentOut]:
    return [_payment_to_out(p) for p in svc.list_payments(db)]


@router.post("/payments/{payment_id}/cancel", response_model=PaymentOut)
def cancel_payment(
    payment_id: int,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> PaymentOut:
    """Makulera a recorded payment (MC 1175.3).

    Append-only: returns the created negative refund row linked back to the
    original via ``cancels_payment_id``. 404 unknown, 409 already-makulerad
    or refund-row target, 410 cancelled invoice."""
    from app.services import payment_edit

    return _payment_to_out(payment_edit.cancel_payment(db, payment_id))
