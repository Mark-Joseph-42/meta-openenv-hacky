"""
Mock Carrier API for tracking shipment/return status.
This is the ONLY way to discover carrier_status (hidden from direct DB queries).
Includes noise entries to test the agent's filtering ability.
"""

CARRIER_DB = {
    "TRK-9928-XZ": {
        "tracking_id": "TRK-9928-XZ",
        "carrier": "FastShip Express",
        "status": "Delivered",
        "delivered_date": "2026-03-27",
        "signed_by": "A. Rivera",
        "delivery_address": "742 Evergreen Terrace"
    },
    "TRK-1042-AB": {
        "tracking_id": "TRK-1042-AB",
        "carrier": "QuickPost",
        "status": "Delivered",
        "delivered_date": "2026-03-22",
        "signed_by": "S. Chen",
        "delivery_address": "100 Main St"
    },
    "TRK-7754-CD": {
        "tracking_id": "TRK-7754-CD",
        "carrier": "FastShip Express",
        "status": "In Transit",
        "delivered_date": None,
        "signed_by": None,
        "delivery_address": "55 Oak Avenue"
    },
    "TRK-3320-EF": {
        "tracking_id": "TRK-3320-EF",
        "carrier": "QuickPost",
        "status": "Delivered",
        "delivered_date": "2026-02-12",
        "signed_by": "A. Rivera",
        "delivery_address": "742 Evergreen Terrace"
    },
    "TRK-8812-GH": {
        "tracking_id": "TRK-8812-GH",
        "carrier": "PremiumLogistics",
        "status": "Delivered",
        "delivered_date": "2026-04-01",
        "signed_by": "M. Katsumi",
        "delivery_address": "200 Sakura Blvd"
    },
    # ── NOISE: Random tracking IDs that return ambiguous status ──
    "TRK-0000-XX": {
        "tracking_id": "TRK-0000-XX",
        "carrier": "Unknown Carrier",
        "status": "Unknown",
        "delivered_date": None,
        "signed_by": None,
        "delivery_address": None
    },
    "TRK-9999-ZZ": {
        "tracking_id": "TRK-9999-ZZ",
        "carrier": "ReturnHub",
        "status": "Return to Sender",
        "delivered_date": None,
        "signed_by": None,
        "delivery_address": "Address Undeliverable"
    },
}


def query_carrier(tracking_id: str) -> dict:
    """Query the carrier API for a tracking ID.
    Returns shipment details or error if not found.
    """
    tracking_id = tracking_id.strip().upper()
    if tracking_id in CARRIER_DB:
        return CARRIER_DB[tracking_id]
    return {
        "error": f"Tracking ID '{tracking_id}' not found in carrier system",
        "suggestion": "Verify the tracking ID format (e.g., TRK-XXXX-XX)"
    }