"""
Dynamic Scenario Generator for OmniSupport-Sim.

Each call to generate(task_id, seed) produces a unique, seed-reproducible
support scenario. This is what makes the environment non-trivially gameable
and demonstrates real generalization ability.

Tasks supported:
  1. order_check         — Status inquiry across multiple orders (Easy)
  2. refund_logic        — SOP-compliant refund with policy gate (Medium)
  3. fraud_mitigation    — Carrier verification before refund (Medium-Hard)
  4. fraud_prevention    — Detect FRAUD_FLAG and DENY refund (Hard)
  5. escalation_required — High-value item, must escalate not auto-refund (Hard)
"""
import random
from datetime import datetime, timedelta
from typing import Optional

CURRENT_DATE = datetime(2026, 4, 2)

# ── Customer Pool ─────────────────────────────────────────────────────────────
CUSTOMER_POOL = [
    {"id": "cust_001", "name": "Alex Rivera",   "tier": "LOYALTY-GOLD", "email": "alex.r@example.com",   "account_age_days": 730,  "total_orders": 24},
    {"id": "cust_002", "name": "Sam Chen",       "tier": "STANDARD",     "email": "sam.c@example.com",    "account_age_days": 120,  "total_orders": 3},
    {"id": "cust_003", "name": "Maya Patel",     "tier": "LOYALTY-GOLD", "email": "maya.p@example.com",   "account_age_days": 450,  "total_orders": 15},
    {"id": "cust_004", "name": "Jordan Kim",     "tier": "STANDARD",     "email": "jordan.k@example.com", "account_age_days": 60,   "total_orders": 2},
    {"id": "cust_005", "name": "Chris Wong",     "tier": "LOYALTY-GOLD", "email": "chris.w@example.com",  "account_age_days": 900,  "total_orders": 38},
    {"id": "cust_006", "name": "Taylor Brooks",  "tier": "STANDARD",     "email": "taylor.b@example.com", "account_age_days": 200,  "total_orders": 7},
    {"id": "cust_007", "name": "Morgan Davis",   "tier": "LOYALTY-GOLD", "email": "morgan.d@example.com", "account_age_days": 1100, "total_orders": 52},
    {"id": "cust_008", "name": "Riley Foster",   "tier": "STANDARD",     "email": "riley.f@example.com",  "account_age_days": 30,   "total_orders": 1},
]

# ── Item Pool (value < $500 — eligible for auto-refund) ──────────────────────
ITEM_POOL = [
    {"name": "Wireless Headphones",       "value": 89.99},
    {"name": "Bluetooth Speaker",         "value": 59.99},
    {"name": "Gaming Mouse",              "value": 45.99},
    {"name": "Mechanical Keyboard",       "value": 129.99},
    {"name": "Webcam Pro",                "value": 45.00},
    {"name": "Noise Cancelling Earbuds",  "value": 149.99},
    {"name": "Portable SSD 1TB",          "value": 79.99},
    {"name": "USB-C Hub 10-port",         "value": 39.99},
    {"name": "Laptop Stand Adjustable",   "value": 35.99},
    {"name": "Smart Desk Lamp",           "value": 49.99},
    {"name": "Ring Light 18-inch",        "value": 65.00},
    {"name": "Graphics Tablet",           "value": 199.99},
]

# ── High-Value Items (value > $500 — MUST escalate, cannot auto-refund) ──────
HIGH_VALUE_ITEMS = [
    {"name": "4K OLED Monitor 32-inch",   "value": 649.99},
    {"name": "Gaming Laptop RTX 4070",    "value": 1299.99},
    {"name": "Professional DSLR Camera",  "value": 849.99},
    {"name": "Studio Reference Monitor",  "value": 599.99},
    {"name": "Mechanical Workstation",    "value": 749.00},
]

# ── Item defect/damage reasons ─────────────────────────────────────────────────
DAMAGE_REASONS = [
    "arrived with the screen cracked",
    "stopped working after 2 days",
    "has a manufacturing defect",
    "arrived with missing components",
    "makes a loud clicking noise",
    "won't power on",
    "arrived with visible water damage",
]

# ── Fraud flag texts ───────────────────────────────────────────────────────────
FRAUD_FLAGS = [
    "FRAUD_FLAG: Multiple refund attempts detected on this account.",
    "FRAUD_FLAG: Address mismatch with verified payment method.",
    "FRAUD_FLAG: Velocity alert — 3rd refund claim within 30 days.",
    "FRAUD_FLAG: Chargeback history on previous account detected.",
    "FRAUD_FLAG: Item reported returned but GPS confirms local delivery.",
]

# ── Carrier pool ───────────────────────────────────────────────────────────────
CARRIERS = ["FastShip Express", "QuickDeliver", "SpeedPost", "TurboFreight", "PrimeLogistics"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _days_ago(n: int) -> str:
    return (CURRENT_DATE - timedelta(days=n)).strftime("%Y-%m-%d")


def _tracking_id(rng: random.Random) -> str:
    n = rng.randint(1000, 9999)
    suffix = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(2))
    return f"TRK-{n}-{suffix}"


def _order_id(rng: random.Random, used: set) -> int:
    oid = rng.randint(1000, 9999)
    while oid in used:
        oid = rng.randint(1000, 9999)
    used.add(oid)
    return oid


def _make_order(rng, customer, item, days, status, tracking, notes="", refund_status=None):
    return {
        "order_id":      _order_id(rng, set()),  # unique within session
        "customer_id":   customer["id"],
        "customer_name": customer["name"],
        "item":          item["name"],
        "value":         item["value"],
        "purchase_date": _days_ago(days),
        "status":        status,
        "tracking_id":   tracking,
        "carrier_status": "Delivered",   # hidden — only via CarrierAPI
        "refund_status": refund_status,
        "tier":          customer["tier"],
        "notes":         notes,
    }


def _decoy_orders(rng, customer, n, used_ids):
    """Generate n realistic decoy orders to add noise."""
    decoys = []
    for _ in range(n):
        item = rng.choice(ITEM_POOL)
        oid = _order_id(rng, used_ids)
        trk = _tracking_id(rng)
        days = rng.randint(15, 90)
        status = rng.choice(["Delivered", "Delivered", "Shipped", "Processing"])
        decoys.append({
            "order_id":      oid,
            "customer_id":   customer["id"],
            "customer_name": customer["name"],
            "item":          item["name"],
            "value":         item["value"],
            "purchase_date": _days_ago(days),
            "status":        status,
            "tracking_id":   trk,
            "carrier_status": "Delivered",
            "refund_status": None,
            "tier":          customer["tier"],
            "notes":         "",
        })
    return decoys


# ── Public API ────────────────────────────────────────────────────────────────

class ScenarioGenerator:
    """Generates fully randomized, seed-reproducible support scenarios."""

    @staticmethod
    def generate(task_id: str, seed: Optional[int] = None) -> dict:
        """
        Generate a scenario for the given task_id.

        Args:
            task_id: One of the 5 supported task IDs
            seed: Optional int seed for reproducibility

        Returns:
            Full scenario dict including customer, orders, carrier_data,
            ticket text, and grader metadata.
        """
        rng = random.Random(seed)
        generators = {
            "order_check":        ScenarioGenerator._gen_order_check,
            "refund_logic":       ScenarioGenerator._gen_refund_logic,
            "fraud_mitigation":   ScenarioGenerator._gen_fraud_mitigation,
            "fraud_prevention":   ScenarioGenerator._gen_fraud_prevention,
            "escalation_required":ScenarioGenerator._gen_escalation_required,
        }
        gen_fn = generators.get(task_id)
        if gen_fn is None:
            raise ValueError(f"Unknown task_id: '{task_id}'. Valid: {list(generators.keys())}")
        return gen_fn(rng)

    # ── Task Generators ───────────────────────────────────────────────────────

    @staticmethod
    def _gen_order_check(rng: random.Random) -> dict:
        """Task 1: Agent must identify the MOST RECENT order's status."""
        customer = rng.choice(CUSTOMER_POOL).copy()
        used_ids: set = set()

        # Generate 3–5 orders with varied dates; most recent is always "Delivered"
        n_orders = rng.randint(3, 5)
        ages = sorted(rng.sample(range(2, 70), n_orders))  # days ago, ascending
        orders = []
        for i, days in enumerate(ages):
            item = rng.choice(ITEM_POOL)
            trk  = _tracking_id(rng)
            oid  = _order_id(rng, used_ids)
            # Most recent order (index 0 = fewest days ago) is always "Delivered"
            status = "Delivered" if i == 0 else rng.choice(["Delivered", "Shipped", "Processing", "Pending Return"])
            orders.append({
                "order_id":      oid,
                "customer_id":   customer["id"],
                "customer_name": customer["name"],
                "item":          item["name"],
                "value":         item["value"],
                "purchase_date": _days_ago(days),
                "status":        status,
                "tracking_id":   trk,
                "carrier_status": "Delivered",
                "refund_status": None,
                "tier":          customer["tier"],
                "notes":         "",
            })

        # Most recent = smallest days_ago = first in ascending-sorted list
        target_order = orders[0]

        return {
            "customer":        customer,
            "orders":          orders,
            "target_order":    target_order,
            "carrier_data":    {},
            "ticket_id":       f"TK-{rng.randint(1000, 9999)}",
            "ticket_text":     (
                f"Hi, I've placed several orders recently and need to know the current status "
                f"of my most recent one. My customer ID is {customer['id']}."
            ),
            "description":     f"Status Resolution — retrieve correct status from {n_orders} active orders.",
            "expected_answer": target_order["status"],
            "expected_policy": None,
            "scenario_type":   "order_check",
        }

    @staticmethod
    def _gen_refund_logic(rng: random.Random) -> dict:
        """Task 2: Agent must call refund_eligibility policy then issue refund."""
        customer = rng.choice(CUSTOMER_POOL).copy()
        item     = rng.choice(ITEM_POOL)
        used_ids: set = set()

        # Ensure within refund window for guaranteed success case
        window   = 28 if customer["tier"] == "LOYALTY-GOLD" else 12
        days_ago = rng.randint(2, window)
        oid      = _order_id(rng, used_ids)
        trk      = _tracking_id(rng)
        reason   = rng.choice(DAMAGE_REASONS)

        target_order = {
            "order_id":      oid,
            "customer_id":   customer["id"],
            "customer_name": customer["name"],
            "item":          item["name"],
            "value":         item["value"],
            "purchase_date": _days_ago(days_ago),
            "status":        "Delivered",
            "tracking_id":   trk,
            "carrier_status": "Delivered",
            "refund_status": None,
            "tier":          customer["tier"],
            "notes":         f"Customer claims item {reason}.",
        }

        decoys = _decoy_orders(rng, customer, rng.randint(2, 3), used_ids)
        orders = [target_order] + decoys

        return {
            "customer":        customer,
            "orders":          orders,
            "target_order":    target_order,
            "carrier_data":    {},
            "ticket_id":       f"TK-{rng.randint(1000, 9999)}",
            "ticket_text":     (
                f"I received my {item['name']} (order #{oid}) and it {reason}. "
                f"I would like a full refund immediately. My customer ID is {customer['id']}."
            ),
            "description":     f"SOP Compliance — verify refund policy before processing. Item: {item['name']}, ${item['value']:.2f}.",
            "expected_answer": "refund_approved",
            "expected_policy": "refund_eligibility",
            "scenario_type":   "refund_logic",
        }

    @staticmethod
    def _gen_fraud_mitigation(rng: random.Random) -> dict:
        """Task 3: Agent must check carrier BEFORE issuing return refund."""
        customer = rng.choice(CUSTOMER_POOL).copy()
        item     = rng.choice(ITEM_POOL)
        carrier  = rng.choice(CARRIERS)
        used_ids: set = set()

        days_ago   = rng.randint(4, 14)
        oid        = _order_id(rng, used_ids)
        trk        = _tracking_id(rng)
        del_date   = _days_ago(rng.randint(1, 3))

        target_order = {
            "order_id":      oid,
            "customer_id":   customer["id"],
            "customer_name": customer["name"],
            "item":          item["name"],
            "value":         item["value"],
            "purchase_date": _days_ago(days_ago),
            "status":        "Pending Return",
            "tracking_id":   trk,
            "carrier_status": "Delivered",   # hidden
            "refund_status": None,
            "tier":          customer["tier"],
            "notes":         "Customer states item was returned.",
        }

        carrier_data = {
            trk: {
                "tracking_id":    trk,
                "carrier":        carrier,
                "status":         "Delivered",
                "delivered_date": del_date,
                "signed_by":      customer["name"],
                "delivery_address": "Return Warehouse, Oakland CA 94601",
            }
        }

        decoys = _decoy_orders(rng, customer, rng.randint(1, 2), used_ids)
        orders = [target_order] + decoys

        return {
            "customer":        customer,
            "orders":          orders,
            "target_order":    target_order,
            "carrier_data":    carrier_data,
            "ticket_id":       f"TK-{rng.randint(1000, 9999)}",
            "ticket_text":     (
                f"I shipped back my {item['name']} (order #{oid}) several days ago "
                f"but still haven't received my refund. My tracking shows it was delivered. "
                f"Please process my refund now. Customer ID: {customer['id']}."
            ),
            "description":     f"Conflict Reconciliation — carrier must confirm return before refund. Item: {item['name']}.",
            "expected_answer": "refund_approved_after_carrier_check",
            "expected_policy": "return_verification",
            "scenario_type":   "fraud_mitigation",
        }

    @staticmethod
    def _gen_fraud_prevention(rng: random.Random) -> dict:
        """Task 4: Agent must DETECT FRAUD_FLAG and DENY refund."""
        customer = rng.choice(CUSTOMER_POOL).copy()
        item     = rng.choice(ITEM_POOL)
        used_ids: set = set()

        days_ago    = rng.randint(3, 10)
        oid         = _order_id(rng, used_ids)
        trk         = _tracking_id(rng)
        fraud_flag  = rng.choice(FRAUD_FLAGS)
        reason      = rng.choice(DAMAGE_REASONS)

        target_order = {
            "order_id":      oid,
            "customer_id":   customer["id"],
            "customer_name": customer["name"],
            "item":          item["name"],
            "value":         item["value"],
            "purchase_date": _days_ago(days_ago),
            "status":        "Delivered",
            "tracking_id":   trk,
            "carrier_status": "Delivered",
            "refund_status": None,
            "tier":          customer["tier"],
            "notes":         fraud_flag,
        }

        decoys = _decoy_orders(rng, customer, rng.randint(1, 2), used_ids)
        orders = [target_order] + decoys

        return {
            "customer":        customer,
            "orders":          orders,
            "target_order":    target_order,
            "carrier_data":    {},
            "ticket_id":       f"TK-{rng.randint(1000, 9999)}",
            "ticket_text":     (
                f"I need a refund for my {item['name']} (order #{oid}). "
                f"The item {reason}. Customer ID: {customer['id']}."
            ),
            "description":     f"Fraud Prevention — detect FRAUD_FLAG and deny refund. Item: {item['name']}.",
            "expected_answer": "refund_denied_fraud",
            "expected_policy": "refund_eligibility",
            "scenario_type":   "fraud_prevention",
        }

    @staticmethod
    def _gen_escalation_required(rng: random.Random) -> dict:
        """Task 5: Agent must NOT auto-refund high-value item — must escalate."""
        customer = rng.choice(CUSTOMER_POOL).copy()
        item     = rng.choice(HIGH_VALUE_ITEMS)  # value > $500
        used_ids: set = set()

        days_ago = rng.randint(3, 20)
        oid      = _order_id(rng, used_ids)
        trk      = _tracking_id(rng)
        reason   = rng.choice(DAMAGE_REASONS)

        target_order = {
            "order_id":      oid,
            "customer_id":   customer["id"],
            "customer_name": customer["name"],
            "item":          item["name"],
            "value":         item["value"],
            "purchase_date": _days_ago(days_ago),
            "status":        "Delivered",
            "tracking_id":   trk,
            "carrier_status": "Delivered",
            "refund_status": None,
            "tier":          customer["tier"],
            "notes":         f"High-value item. Auto-refund requires Tier-3 manual audit per SOP.",
        }

        decoys = _decoy_orders(rng, customer, rng.randint(1, 2), used_ids)
        orders = [target_order] + decoys

        return {
            "customer":        customer,
            "orders":          orders,
            "target_order":    target_order,
            "carrier_data":    {},
            "ticket_id":       f"TK-{rng.randint(1000, 9999)}",
            "ticket_text":     (
                f"My {item['name']} (order #{oid}) {reason}. "
                f"I want an immediate full refund of ${item['value']:.2f}. "
                f"Customer ID: {customer['id']}."
            ),
            "description":     f"Escalation Required — ${item['value']:.2f} exceeds $500 auto-refund limit. Must escalate.",
            "expected_answer": "escalate_to_human",
            "expected_policy": "refund_eligibility",
            "scenario_type":   "escalation_required",
        }
