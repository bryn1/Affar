"""Shared lifecycle guards for the draft-editable rule (MC 11499 rank 6).

The same guard — *verb* is allowed on a draft only; ``cancelled`` is terminal
(410), any other status is 409 — was declared twice (services.orders and
services.purchase_edit). ONE copy lives here; each caller passes its own
entity label, so the detail messages stay exactly as the contract tests pin
them.
"""

from fastapi import HTTPException, status as http_status


def require_draft_editable(entity_status: str, entity_label: str, verb: str) -> None:
    """Guard: *verb* is allowed on a draft only; other statuses explain why."""
    if entity_status == "draft":
        return
    if entity_status == "cancelled":
        raise HTTPException(
            status_code=http_status.HTTP_410_GONE,
            detail=f"{entity_label} is cancelled; it cannot be {verb}ed",
        )
    raise HTTPException(
        status_code=http_status.HTTP_409_CONFLICT,
        detail=f"{entity_label} is {entity_status!r}; only a draft can be {verb}ed",
    )
