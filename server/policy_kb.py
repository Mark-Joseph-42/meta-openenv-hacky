"""
Semi-structured Policy Knowledge Base.
Agent queries this via VerifyPolicy(topic) before taking actions.
"""

POLICY_KB = {
    "refund_eligibility": {
        "policy_id": "POL-REF-001",
        "title": "Standard Refund Eligibility",
        "conditions": [
            "Item must be purchased within the last 14 days",
            "Item value must be under $500"
        ],
        "both_conditions_required": True,
        "exceptions": [
            "LOYALTY-GOLD members: refund window extended to 30 days",
            "PLATINUM members: refund window extended to 30 days, value limit increased to $1000"
        ],
        "process": "Verify eligibility → Issue refund via ExecuteAction(cmd='issue_refund')",
        "violation_penalty": "Issuing refund without verifying eligibility is an SOP violation"
    },
    "escalation_protocol": {
        "policy_id": "POL-ESC-001",
        "title": "Escalation Protocol",
        "triggers": [
            "Refund amount exceeds $200",
            "Account has active fraud flag",
            "Customer has filed 3+ complaints in 30 days"
        ],
        "action": "Route to Tier-3 supervisor. Do NOT auto-resolve.",
        "note": "LOYALTY-GOLD and PLATINUM members may bypass $200 threshold"
    },
    "return_verification": {
        "policy_id": "POL-RET-001",
        "title": "Return Verification Process",
        "required_steps": [
            "1. Locate tracking_id in the order record",
            "2. Query CarrierAPI with the tracking_id to get delivery confirmation",
            "3. Verify carrier_status == 'Delivered' (confirms carrier received the return)",
            "4. Only THEN issue refund via ExecuteAction"
        ],
        "critical_rule": "Issuing a refund WITHOUT confirming carrier delivery status results in SCORE 0.0",
        "note": "This prevents 'happy path' hallucinations where agents skip verification"
    },
    "shipping_change": {
        "policy_id": "POL-SHIP-001",
        "title": "Shipping Address Change",
        "conditions": [
            "Order must be in 'Processing' status",
            "Cannot change after 'Shipped' status"
        ],
        "action": "ExecuteAction(cmd='change_shipping', params={'order_id': ..., 'new_address': ...})"
    },
    "fraud_investigation": {
        "policy_id": "POL-FRD-001",
        "title": "Fraud Investigation",
        "indicators": [
            "New account (<30 days) with high-value purchase",
            "Multiple failed payment attempts",
            "Mismatched shipping/billing addresses"
        ],
        "action": "Flag for manual review. Do NOT process refund or shipping changes."
    }
}


def lookup_policy(topic: str) -> dict:
    """Retrieve policy rules for a given topic.
    Returns the policy dict or an error if topic not found.
    """
    # Normalize the input topic
    topic_lower = topic.lower().strip().replace(" ", "_")
    
    # Check for exact match first
    if topic_lower in POLICY_KB:
        return POLICY_KB[topic_lower]
    
    # Fuzzy match - check if topic is contained in key or vice versa
    for key in POLICY_KB:
        if topic_lower in key or key in topic_lower:
            return POLICY_KB[key]
    
    # No match found
    return {
        "error": f"Policy topic '{topic}' not found",
        "available_topics": list(POLICY_KB.keys())
    }