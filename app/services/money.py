"""One line-money arithmetic rule (MC 11499 rank 10).

qty * price, quantized to two decimals, appeared in every line-building path
(order create, order edit, PO line edit, invoice correction, invoice-from-order
copy). All of them call ``line_money`` — one implementation per concern, and
all money stays Decimal (I7).
"""

from decimal import Decimal


def line_money(qty: int, price) -> Decimal:
    """Return qty * *price* quantized to two decimals (all-Decimal math, I7)."""
    return (Decimal(qty) * Decimal(price)).quantize(Decimal("0.01"))
