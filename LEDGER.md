# Affär — the complete business system (fullstack ERP)

**STATUS 2026-10-27 (clean-code refactor run, wave R4 docs/repo hygiene):** the
product works and is published at sibbamala.com/affar (master 0a47ddd; the live
site serves master's committed dist bundle `index-3lA3NMGh.js` — mirror IN SYNC,
re-probed 2026-10-27). The clean-code audit (MC 11449) and its fix waves R1b/R2/
R3a/R3b/R4 are committed on branch `refactor/cleancode-11449`; this branch's
dist bundle is `index-DEb6NQQN.js` (goes live when the branch merges and the
vm106 mirror re-syncs). Suite: 269 pytest collected, green on this tree.
Ledger translated to English per the owner ruling 2026-10-08 (this commit).

**GOAL:** A complete, working business system (fullstack ERP) with order
management (incl. international tracking, POC), invoices, payments, customer
data and purchasing, in a frontend covering the user types a complete system
requires. Built against an existing ERP as a template (ERPNext) and hosted on
vm106.

**ACCEPTANCE (phase 2+):** the app serves at sibbamala.com/affar (after the
repo was made public), fullstack works end-to-end, the frontend covers the
user types, and a real flow (order→invoice→payment, resp. customer→purchase)
is proven with real calls. — MET (QA 2026-09-24 + live probes since).

**Owner decisions (2026-08-25):**
1. Base choice delegated to the orchestrator — "pick a good base", "the
   simplest that is scalable".
2. Fullstack (frontend + backend + database).
3. A plan in several phases → phased build, MVP first.
4. Simplest scalable solution → FastAPI + SQLAlchemy + SQLite (Postgres
   growth path), React (Vite) frontend, JSON REST API.
5. Throwaway → hosted on vm106 per skills (public auto-lane sibbamala.com/affar).

**Owner ruling (2026-10-27, on audit rank 1, VERBATIM):** "Passwords are
supposed to be published since this is a poc. Fix the rest" — the seeded demo
passwords are INTENTIONAL-POC and stay published; everything else the audit
found is fixed (waves R1b–R4 below).

**Template:** ERPNext (Frappe) domain model — the canonical open-source full
ERP with exactly these modules (Order, Invoice, Payment, Customer, Supplier,
Item, Purchase, Delivery/tracking).

**Scope guard:** demo business system. "Payment" = registration of received
payments (simulated), NO real payment gateway / no real money. Customer data =
demo/fictional. Public since 2026-09 via the external-exposure gate's public
auto-lane (vm106, sibbamala.com/affar).

**User types (complete system):** Admin (users, roles, system); Sales/orders
(create/edit orders, tracking); Finance/invoicing (invoices, payments);
Purchasing (suppliers, purchase orders); Customer view (track own order via
tracking id).

## Phase 2b + tracking-write done (2026-08-26)
C1-config hard-fail, customers module, React/Vite frontend, hosting.yaml
(port 8110), tracking write-side C21. 248 pytest green at the time
(audit-verified 2026-09-23), E2E verified live. Next at the time: publishing
to vm106 (phase 2c) via GitHub remote + reconciler lane.

## Security + logic audit PASS (2026-09-23, MC 1325)
Delegated audit (2 subagents) of master 709b319+cbd5a25: 0×P0/P1/P2. P3s:
public demo passwords (intentional PoC — re-confirmed as such by the owner
ruling 2026-10-27 above), CORS default '*' (env fix), missing
duplicate-invoice_no test, LEDGER test counter stale (fixed then). Startup
migration 1323.1 landed in master (cbd5a25); mirror 7cdbf5b already carried
the fix. Evidence: /srv/workspace/affar-audit-20260923/ — ARCHIVE-ONLY: that
vm105-era path is gone (host destroyed 2026-10-14); findings are on the MC cards.

## Full-function QA + F1/F6 fixes (2026-09-24, MC 1349/1350/1351)
QA (UI + API E2E, 39 steps): PASS with findings. F3–F5 contract drift landed
2026-09-23 (6c3e14d + 3fed96f, 251 pytest). F1: payment against an already-
paid invoice → 409 (owner decision 2026-09-24, option A); the 1175.3 refund
flow rewritten to cancel-first (56b48c0). F6: Payments date column reads
paid_at (9de1c3e, dist rebuilt). F2 classified as a design choice: PO
re-receive is an idempotent 200 (guard in purchase.py, no double stock-in) —
kept. 252 pytest green on merged master (orchestrator-verified). A mirror lag
was recorded here at the time; it was since resolved — re-checked 2026-10-27,
live serves master's current committed bundle (index-3lA3NMGh.js): the mirror
policy works, the kick happened. Evidence:
/srv/workspace/affar-audit-20260923/ — ARCHIVE-ONLY (vm105-era, host destroyed).

## Clean-code audit (2026-10-27, MC 11449 + 11450/11457/11458)
Findings-only audit per the clean-code doctrine MC 11318 (run
`.audits/20261027-1420-cleancode/`, host-local): 3 dimensions (hygiene,
design, security) → overall verdict FIX; ranked findings 1–23 + 14 P4 rows;
zero files >400 lines (drift/duplication, not size, was the story). Rank 1
(published seed passwords) closed by the owner ruling quoted above.

## Clean-code refactor waves R1b–R4 (2026-10-27, MC 11449)
Branch `refactor/cleancode-11449`, per-wave commits, suite green throughout:
- R1b (MC 11468): JWT revocation — auth deps re-read the live User row per
  request (rank 5).
- R2 (MC 11469): contract drift — PO row `total` (rank 2), Förfallo column +
  dead name fallbacks deleted (ranks 3–4), qty bound + CORS-on-429 (P4s).
- R3a (MC 11499): backend de-duplication — shared lifecycle guard,
  line-items/money helpers, app/roles.py + app/projections.py (ranks 6–11, 13).
- R3b (MC 11502): frontend de-dup — formatWhen/useResource/can() gating +
  dead api.js wrapper prune, dist rebuilt (ranks 12, 18, 19 + P4 rows);
  bundle index-DEb6NQQN.js.
- R4 (MC 11516, this commit): docs + repo hygiene — LEDGER de-stale + English
  translation (rank 14); mock-server.mjs deleted (rank 21); .gitignore
  versions the .tmp/.playwright-mcp/.audits exclusions (rank 22); config.py
  fail-fast on unset AFFAR_DATABASE_URL (rank 23); vite comment, hosting.yaml
  self-contained excludes, retired-account refs updated to bryn1 (P4); orders create
  flush+one-commit and catalog_adjust bridge removal, three more dead api.js
  wrappers pruned (P4). Suite: 269 pytest collected green.
