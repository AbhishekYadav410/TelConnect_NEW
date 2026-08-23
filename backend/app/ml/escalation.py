"""Escalation Risk Assessment Component.

Evaluates customer churn intent, regulatory threats, repeat contact patterns,
and negative sentiment intensity to predict escalation risk.

Status-aware: Closed or resolved complaints are never marked as active escalations.
"""
import logging
import re
from typing import List, Optional, Tuple

from ..services.etl import normalize_hinglish

logger = logging.getLogger(__name__)

# Trigger keyword dictionaries
CHURN_SIGNALS = {
    "port", "switch", "cancel", "disconnect my", "leave", "close my account",
    "change provider", "jio", "airtel", "vi ", "bsnl", "last chance", "leaving",
    "porting out", "surrender connection", "terminate"
}

REGULATORY_SIGNALS = {
    "trai", "consumer court", "legal", "complaint forum", "ombudsman", "sue",
    "lawyer", "advocate", "police", "court notice", "fraud", "scam", "fir"
}

REPEAT_SIGNALS = {
    "again", "still", "second time", "third time", "repeatedly", "many times",
    "baar baar", "already complained", "no response", "no update", "pending for days",
    "unresolved", "not fixed yet", "called yesterday", "follow up"
}


def _hits(text: str, words: set) -> int:
    return sum(1 for w in words if w in text)


def predict_escalation(
    text: str,
    sentiment_score: float = 0.0,
    urgency: int = 0,
    status: str = "open",
    repeat_count: int = 0
) -> Tuple[str, float, str, List[str]]:
    """Calculate escalation risk tier, score, and contributing reasons.
    
    Returns:
        (escalation_risk, escalation_risk_score, escalation_reason, factors_list)
        - escalation_risk: "Low" | "Medium" | "High"
        - escalation_risk_score: float in [0.0, 1.0]
        - escalation_reason: human-readable explanation
        - factors_list: list of individual triggered factor descriptions
    """
    # Inactive status check (Closed / Resolved tickets must not be active escalations)
    if status.lower() in ("closed", "resolved", "resolved_pending_confirmation"):
        return "Low", 0.05, "Ticket is closed/resolved (no active escalation)", []

    norm = normalize_hinglish(text.lower())
    factors = []
    base_risk = 0.15

    # 1. Sentiment factor
    if sentiment_score < -0.3:
        base_risk += 0.25
        factors.append("Strongly negative customer sentiment")
    elif sentiment_score < -0.1:
        base_risk += 0.10
        factors.append("Negative customer tone")

    # 2. Urgency factor
    if urgency > 0:
        base_risk += 0.15
        factors.append("Urgent / emergency wording")

    # 3. Churn indicators
    if _hits(norm, CHURN_SIGNALS) > 0:
        base_risk += 0.25
        factors.append("Churn risk: customer mentions switching/porting/cancellation")

    # 4. Regulatory / Legal indicators
    if _hits(norm, REGULATORY_SIGNALS) > 0:
        base_risk += 0.30
        factors.append("Regulatory escalation threat (TRAI / Consumer Court / Ombudsman)")

    # 5. Repeat complaint indicators
    if _hits(norm, REPEAT_SIGNALS) > 0 or repeat_count > 1:
        base_risk += 0.20
        factors.append("Repeat complaint history / persistent unresolved issue")

    score = round(min(1.0, max(0.05, base_risk)), 3)

    # Classify into Low / Medium / High
    if score >= 0.65:
        tier = "High"
    elif score >= 0.40:
        tier = "Medium"
    else:
        tier = "Low"

    reason_text = "; ".join(factors) if factors else "Standard baseline risk"
    return tier, score, reason_text, factors


# Semantic alias matching legacy interface
def score_escalation_risk(text: str, sentiment: float, urgency: int) -> Tuple[float, List[str]]:
    """Legacy compatibility adapter returning (risk_score, factors_list)."""
    _tier, score, _reason, factors = predict_escalation(text, sentiment_score=sentiment, urgency=urgency)
    return score, factors
