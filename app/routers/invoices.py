"""Invoicing routers (contract C16) — HTTP surface for invoices.

    POST   /api/orders/{id}/invoice  -> InvoiceOut   [admin, finance]
    GET    /api/invoices             -> list[InvoiceOut]
    GET    /api/invoices/{id}        -> InvoiceOut (with lines + payments)
    PATCH  /api/invoices/{id}          InvoicePatch -> InvoiceOut  [admin, finance]
    PATCH  /api/invoices/{id}/status {status} -> InvoiceOut   (+ "cancel" = makulera)

MC 1175.2: an issued (not yet paid) invoice is line-editable — the wire
carries {item_id?, description?, qty} only, prices stay server-owned (C14).

This surface only projects ORM rows onto InvoiceOut — it never returns raw ORM
objects; the projection itself is shared with the payments router via
app.projections (MC 11499 rank 9). Issue (create from confirmed order) and status transitions live in the
service layer; payments/reconcile are the C17 router under /api/invoices/{id}/.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import roles
from app.auth import require_role
from app.database import get_session
from app.projections import invoice_to_out
from app.schemas.invoice import InvoiceOut, InvoicePatch, InvoiceStatusIn

from app.services import invoicing as svc

router = APIRouter(prefix="/api", tags=["invoices"])


@router.post("/orders/{order_id}/invoice", response_model=InvoiceOut)
def create_invoice(
    order_id: int,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> InvoiceOut:
    invoice = svc.create_invoice_from_order(db, order_id)
    return invoice_to_out(invoice)


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> list[InvoiceOut]:
    return [invoice_to_out(i) for i in svc.list_invoices(db)]


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> InvoiceOut:
    invoice = svc.get_invoice_or_404(db, invoice_id)
    return invoice_to_out(invoice)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
def patch_invoice(
    invoice_id: int,
    body: InvoicePatch,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> InvoiceOut:
    """Replace the line set of a NOT-YET-PAID invoice (MC 1175.2).

    Prices never come from the client (C14): they carry over per item from
    the old server-owned lines, else the item's catalog price."""
    from app.services import invoice_edit

    invoice = invoice_edit.replace_invoice_lines(db, invoice_id, body.lines)
    return invoice_to_out(invoice)


@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceOut)
def patch_status(
    invoice_id: int,
    body: InvoiceStatusIn,
    db: Session = Depends(get_session),
    _auth=Depends(require_role(roles.FINANCE)),
) -> InvoiceOut:
    invoice = svc.update_status(db, invoice_id, body.status)
    return invoice_to_out(invoice)
