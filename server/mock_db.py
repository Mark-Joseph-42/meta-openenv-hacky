"""
Mock CRM / Order Database.

Upgraded: load_scenario() replaces the static initial state with a
dynamically generated scenario from ScenarioGenerator.

Hidden-state design preserved: carrier_status is NEVER exposed via
search_orders() — agents MUST use the CarrierAPI (search_db with TRK-* id).
"""
import copy
from datetime import datetime, timedelta

NOW = datetime(2026, 4, 2)

# ── Static fallback DB (used only if load_scenario() is never called) ─────────
_FALLBACK_ORDERS = [
    {
        "order_id": 4829, "customer_id": "cust_001", "customer_name": "Alex Rivera",
        "item": "Wireless Headphones", "value": 89.99, "purchase_date": "2026-03-25",
        "status": "Pending Return", "tracking_id": "TRK-9928-XZ",
        "carrier_status": "Delivered", "refund_status": None,
        "tier": "LOYALTY-GOLD", "notes": "Customer claims item arrived damaged.",
    },
    {
        "order_id": 5510, "customer_id": "cust_001", "customer_name": "Alex Rivera",
        "item": "Webcam Pro", "value": 45.00, "purchase_date": "2026-04-01",
        "status": "Delivered", "tracking_id": "TRK-4412-PP",
        "carrier_status": "Delivered", "refund_status": None,
        "tier": "LOYALTY-GOLD", "notes": "",
    },
    {
        "order_id": 3901, "customer_id": "cust_001", "customer_name": "Alex Rivera",
        "item": "Bluetooth Speaker", "value": 59.99, "purchase_date": "2026-02-10",
        "status": "Delivered", "tracking_id": "TRK-3320-EF",
        "carrier_status": "Delivered", "refund_status": None,
        "tier": "LOYALTY-GOLD", "notes": "",
    },
]

_FALLBACK_CUSTOMERS = {
    "cust_001": {
        "customer_id": "cust_001", "name": "Alex Rivera", "email": "alex.r@example.com",
        "tier": "LOYALTY-GOLD", "account_age_days": 730, "total_orders": 24,
        "lifetime_value": 2450.00, "complaints": 1, "last_interaction": "2 mins ago",
    },
}


class MockDB:
    """Resettable mock database with hidden-state design."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Restore database to clean fallback state."""
        self.orders    = copy.deepcopy(_FALLBACK_ORDERS)
        self.customers = copy.deepcopy(_FALLBACK_CUSTOMERS)

    def load_scenario(self, scenario: dict):
        """
        Load scenario data into the DB. Called by environment on reset().
        Builds orders list and customer profile from the generated scenario.
        """
        customer = scenario["customer"]
        orders   = scenario["orders"]

        # Build customer record
        self.customers = {
            customer["id"]: {
                "customer_id":      customer["id"],
                "name":             customer["name"],
                "email":            customer.get("email", ""),
                "tier":             customer["tier"],
                "account_age_days": customer.get("account_age_days", 365),
                "total_orders":     customer.get("total_orders", 5),
                "lifetime_value":   sum(o["value"] for o in orders),
                "complaints":       0,
                "last_interaction": "Just now",
            }
        }

        # Build orders list from scenario (deep copy to allow mutation)
        self.orders = copy.deepcopy(orders)

    def search_orders(self, query: str) -> list:
        """Search orders by customer_id, order_id, item name, or status.
        Returns orders WITHOUT carrier_status (hidden state — use CarrierAPI).
        """
        query_lower = query.lower().strip()
        results = []
        for order in self.orders:
            searchable = (
                f"{order['order_id']} {order['customer_id']} "
                f"{order.get('customer_name', '')} {order['item']} {order['status']}"
            ).lower()
            if query_lower in searchable:
                visible = {k: v for k, v in order.items() if k != "carrier_status"}
                results.append(visible)
        return results if results else [{"error": f"No orders found matching '{query}'"}]

    def get_customer_history(self, customer_id: str) -> dict:
        """Get customer profile and their order summaries."""
        customer = self.customers.get(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
        orders = [
            {
                "order_id":     o["order_id"],
                "item":         o["item"],
                "status":       o["status"],
                "value":        o["value"],
                "purchase_date":o["purchase_date"],
            }
            for o in self.orders if o["customer_id"] == customer_id
        ]
        return {**customer, "orders": orders}

    def update_refund_status(self, order_id: int, status: str) -> dict:
        """Update refund status for an order."""
        for order in self.orders:
            if order["order_id"] == order_id:
                order["refund_status"] = status
                return {
                    "success":       True,
                    "order_id":      order_id,
                    "refund_status": status,
                    "amount":        order["value"],
                    "item":          order["item"],
                }
        return {"error": f"Order {order_id} not found"}

    def get_order_by_id(self, order_id: int) -> dict | None:
        """Get a specific order by ID (internal use, includes hidden fields)."""
        for order in self.orders:
            if order["order_id"] == order_id:
                return order
        return None

    def get_snapshot(self) -> dict:
        """Full DB snapshot for grading (includes carrier_status)."""
        return {
            "orders":    copy.deepcopy(self.orders),
            "customers": copy.deepcopy(self.customers),
        }