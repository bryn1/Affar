"""Wire-contract pins — MC-C2 (11469), killing the CLASS behind ranks 2-4.

Three separate shipped bugs shared one cause: a list view read a field the
wire never carried (Invoices.jsx "Förfallo" on r.due_date; Orders.jsx on
r.customer_name; Purchase.jsx on r.supplier_name / r.total before the
server summed it). Each pin below names the fields a view reads on a row
of a list route and checks them against the schema that route serializes —
a rename or removal on either side of the wire fails THIS file, not the
browser. When a view starts reading a new row field, add it to the matching
set AND to the schema; that pairing is the point of the test.
"""

from app.routers import invoices as invoices_router
from app.routers import orders as orders_router
from app.routers import purchase as purchase_router
from app.schemas.invoice import InvoiceLineOut, InvoiceOut
from app.schemas.order import OrderLineOut, OrderOut
from app.schemas.payment import PaymentOut
from app.schemas.purchase import PurchaseOrderLineOut, PurchaseOrderOut

# src/views/Invoices.jsx — columns + row actions on GET /api/invoices rows.
INVOICE_ROW_FIELDS = {"id", "order_id", "status", "total"}
# src/views/Invoices.jsx — edit-form reads on invoice lines (detail + edit).
INVOICE_LINE_FIELDS = {"item_id", "description", "qty"}
# src/views/Invoices.jsx — payment panel reads on InvoiceOut.payments.
INVOICE_PAYMENT_FIELDS = {"id", "amount", "method", "cancels_payment_id"}

# src/views/Orders.jsx — columns + startEdit reads on GET /api/orders rows.
ORDER_ROW_FIELDS = {"id", "customer_id", "status", "total", "created_at", "lines"}
# src/views/Orders.jsx — edit-form reads on order.lines entries.
ORDER_LINE_FIELDS = {"item_id", "qty"}

# src/views/Purchase.jsx — columns + startEdit on GET /api/purchase-orders.
PURCHASE_ROW_FIELDS = {"id", "supplier_id", "status", "total", "lines"}
# src/views/Purchase.jsx — edit-form reads on po.lines entries.
PURCHASE_LINE_FIELDS = {"item_id", "qty", "unit_cost"}


def _assert_pinned(view_fields, schema):
    missing = view_fields - schema.model_fields.keys()
    assert not missing, f"view reads {sorted(missing)}, absent from {schema.__name__}"


def test_invoice_list_wire_contract():
    _assert_pinned(INVOICE_ROW_FIELDS, InvoiceOut)
    _assert_pinned(INVOICE_LINE_FIELDS, InvoiceLineOut)
    _assert_pinned(INVOICE_PAYMENT_FIELDS, PaymentOut)
    # The "Förfallo" column read a due date the aggregate never had
    # (MC-C2 rank 2); the fix deleted the claim — keep it deleted.
    assert "due_date" not in InvoiceOut.model_fields


def test_order_list_wire_contract():
    _assert_pinned(ORDER_ROW_FIELDS, OrderOut)
    _assert_pinned(ORDER_LINE_FIELDS, OrderLineOut)
    # Dead fallback removed (MC-C2 rank 3) — the backend never sends a name.
    assert "customer_name" not in OrderOut.model_fields


def test_purchase_list_wire_contract():
    _assert_pinned(PURCHASE_ROW_FIELDS, PurchaseOrderOut)
    _assert_pinned(PURCHASE_LINE_FIELDS, PurchaseOrderLineOut)
    assert "supplier_name" not in PurchaseOrderOut.model_fields


def test_list_routes_serialize_the_pinned_schemas():
    # The pins above only bind while the list routes serialize these exact
    # schemas — swap a route's response_model and this fails, by design.
    models = {
        path: route.response_model
        for router, path in (
            (invoices_router.router, "/api/invoices"),
            (orders_router.router, "/api/orders"),
            (purchase_router.router, "/api/purchase-orders"),
        )
        for route in router.routes
        if getattr(route, "path", None) == path
        and "GET" in getattr(route, "methods", set())
        and getattr(route, "response_model", None) is not None
    }
    assert models["/api/invoices"] == list[InvoiceOut]
    assert models["/api/orders"] == list[OrderOut]
    assert models["/api/purchase-orders"] == list[PurchaseOrderOut]
