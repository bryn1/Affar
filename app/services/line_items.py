"""Shared resolve step of the line-replacement skeleton (MC 11499 rank 7).

The three replacement paths (order draft edit, PO draft edit, invoice
correction) opened with the same copied moves: resolve every line's item_id
to its Item in ONE query, and treat an unknown id as a 404 that rolls the
whole replacement back. Those moves live here (public names — a shared
module, not another router's private symbol); each service keeps its own
price-ownership rule (C14 snapshot / C18 wire-supplied / C16 carry-over —
deliberately NOT merged, the audit refuted unifying them).
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Item


def resolve_items(db: Session, lines) -> dict[int, Item]:
    """Return {item_id: Item} for *lines* in one O(n) query.

    Lines without an item_id (invoice free lines) are skipped.
    """
    item_ids = [ln.item_id for ln in lines if ln.item_id is not None]
    return {it.id: it for it in db.query(Item).filter(Item.id.in_(item_ids)).all()}


def item_or_404(db: Session, item_map: dict[int, Item], item_id: int) -> Item:
    """Return the resolved item; an unknown id rolls the edit back and 404s."""
    item = item_map.get(item_id)
    if item is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item
