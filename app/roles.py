"""Named role sets for every protected surface (MC 11499 rank 11).

The audit counted twelve hand-declared ``[...]`` lists feeding ``require_role``
across routers and services. They collapsed to six distinct sets; each one is
declared ONCE here, named by what it guards, so a role change is one line and
grep-verifiable. The values mirror the contract lists exactly (C6/C8/C9/C12/
C13/C16/C17/C19/C21) — the customer role appears in none of them. The frontend
PERMS mirror is wave R3b (src/ untouched by this wave).
"""

# User administration only (C6 admin surface).
ADMIN_ONLY = ["admin"]

# Money surfaces: invoicing (C16), payments/reconcile (C17) and the sales
# report (the money view is finance business).
FINANCE = ["admin", "finance"]

# Sales-side staff: placing and managing internal orders (C13/C14) and
# advancing deliveries (C21). Finance reads and confirms but never edits.
SALES_OPS = ["admin", "sales", "finance"]

# Narrow edit surface on the sales side: draft order line/status edits
# (MC 1175.1) and customer master data (C9). Finance reads, never edits.
SALES_EDIT = ["admin", "sales"]

# Catalog surface (C8): every staff role, customer deliberately absent.
ALL_STAFF = ["admin", "sales", "finance", "procurement"]

# Purchase side (C12/C19) and the stock report: procurement business.
PROCUREMENT = ["admin", "procurement"]
