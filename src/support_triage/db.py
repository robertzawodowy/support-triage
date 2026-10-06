"""A fake in-memory 'database' so the tutorial runs without any infrastructure."""
from dataclasses import dataclass, field

ORDERS = {
    "A-1001": {"customer_id": "c1", "status": "shipped", "eta": "2026-10-09", "total": 59.90},
    "A-1002": {"customer_id": "c1", "status": "delivered", "eta": None, "total": 120.00},
    "A-2001": {"customer_id": "c2", "status": "processing", "eta": "2026-10-14", "total": 15.50},
}

FAQ = {
    "refund": "Refunds are issued to the original payment method within 5-7 business days.",
    "password": "Use 'Forgot password' on the login page; the reset link is valid for 1 hour.",
    "shipping": "Standard shipping takes 3-5 business days; express takes 1-2.",
}


@dataclass
class SupportDB:
    """Dependency injected into tools via RunContext.deps."""

    orders: dict = field(default_factory=lambda: dict(ORDERS))
    faq: dict = field(default_factory=lambda: dict(FAQ))

    def get_order(self, order_id: str, customer_id: str) -> dict | None:
        order = self.orders.get(order_id)
        # Never leak another customer's order
        if order and order["customer_id"] == customer_id:
            return order
        return None

    def search_faq(self, query: str) -> list[str]:
        q = query.lower()
        return [text for key, text in self.faq.items() if key in q]
