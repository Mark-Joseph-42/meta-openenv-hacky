"""
Mock Carrier API — dynamic, scenario-aware.

Now reads from the scenario's carrier_data dict (injected at episode start)
instead of a static lookup table.

Hidden-state: carrier_status is never in search_db results.
Agents MUST call search_db with a "TRK-*" query to reach this API.
"""

# ── Static noise entries (always present, test agent filtering) ───────────────
_NOISE = {
    "TRK-0000-XX": {
        "tracking_id":    "TRK-0000-XX",
        "carrier":        "Unknown Carrier",
        "status":         "Unknown",
        "delivered_date": None,
        "signed_by":      None,
        "delivery_address": None,
    },
    "TRK-9999-ZZ": {
        "tracking_id":    "TRK-9999-ZZ",
        "carrier":        "ReturnHub",
        "status":         "Return to Sender",
        "delivered_date": None,
        "signed_by":      None,
        "delivery_address": "Address Undeliverable",
    },
}


def query_carrier(tracking_id: str, scenario_carrier_data: dict | None = None) -> dict:
    """
    Query the carrier API for a tracking ID.

    Args:
        tracking_id: The TRK-* identifier to look up
        scenario_carrier_data: Dynamic data from the active scenario
                                (injected by the environment on each step)

    Returns:
        Carrier record dict, or error dict if not found
    """
    tid = tracking_id.strip().upper()

    # 1. Check scenario-specific carrier data first (dynamic)
    if scenario_carrier_data:
        for key, record in scenario_carrier_data.items():
            if key.upper() == tid:
                return record

    # 2. Fall back to static noise (always present)
    if tid in _NOISE:
        return _NOISE[tid]

    return {
        "error":      f"Tracking ID '{tid}' not found in carrier system",
        "suggestion": "Verify the tracking ID format (e.g., TRK-XXXX-XX)",
    }