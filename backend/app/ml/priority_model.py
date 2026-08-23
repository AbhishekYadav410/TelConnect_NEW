"""Priority Scoring & SLA Determination Component.

Implements an explainable, configurable multi-factor priority scoring engine
combining Category weight, Sentiment polarity, Escalation risk, Urgency indicators,
and Complaint age.
"""
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Configurable category impact weights
CATEGORY_WEIGHTS: Dict[str, float] = {
    "network": 0.90,
    "billing": 0.70,
    "service": 0.60,
    "device": 0.50,
    "other": 0.30,
}

# SLA Target Resolution Hours by Priority Tier
SLA_HOURS = {
    "P1": 4,   # Critical / High Priority (4h)
    "P2": 8,   # High Priority (8h)
    "P3": 24,  # Medium Priority (24h)
    "P4": 72,  # Low Priority (72h)
}


def priority_label(score: float) -> str:
    """Map continuous priority score [0.0, 1.0] to operational ITIL priority tags."""
    if score >= 0.75:
        return "P1"
    if score >= 0.55:
        return "P2"
    if score >= 0.35:
        return "P3"
    return "P4"


def priority_tier(score: float) -> str:
    """Map continuous priority score to standard Low / Medium / High classification."""
    if score >= 0.65:
        return "High"
    if score >= 0.40:
        return "Medium"
    return "Low"


def sla_deadline_for(score: float, created_iso: Optional[str] = None) -> str:
    """Compute exact ISO timestamp for SLA deadline based on priority score."""
    label = priority_label(score)
    hours = SLA_HOURS.get(label, 24)
    if created_iso:
        try:
            base = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            base = datetime.now(timezone.utc)
    else:
        base = datetime.now(timezone.utc)

    deadline = base + timedelta(hours=hours)
    return deadline.isoformat()


def calculate_priority(
    category: str,
    sentiment_score: float = 0.0,
    urgency: int = 0,
    escalation_risk_score: float = 0.15,
    escalation_factors: Optional[List[str]] = None,
    category_confidence: float = 1.0,
    complaint_age_hours: float = 0.0,
    status: str = "open"
) -> Tuple[str, float, str, str, List[Dict[str, Any]]]:
    """Calculate explainable multi-factor priority score, tier, and rationale.
    
    Returns:
        (priority_tier, priority_score, priority_label, priority_reason, priority_factors)
        - priority_tier: "Low" | "Medium" | "High"
        - priority_score: float in [0.0, 1.0]
        - priority_label: "P1" | "P2" | "P3" | "P4"
        - priority_reason: human-readable explanation
        - priority_factors: structured list of factor weights
    """
    cat_base = CATEGORY_WEIGHTS.get(category.lower(), 0.30)
    factors: List[Dict[str, Any]] = []
    
    # 1. Category Impact (35% weight)
    cat_contrib = round(cat_base * 0.35, 3)
    factors.append({
        "factor": f"category: {category.lower()}",
        "weight": cat_contrib
    })
    score = cat_contrib

    # 2. Escalation Risk (35% weight)
    risk_contrib = round(escalation_risk_score * 0.35, 3)
    risk_desc = f"escalation risk ({', '.join(escalation_factors)})" if escalation_factors else "escalation risk (baseline)"
    factors.append({
        "factor": risk_desc,
        "weight": risk_contrib
    })
    score += risk_contrib

    # 3. Negative Sentiment Impact (20% weight)
    neg_component = max(0.0, -sentiment_score) * 0.20
    neg_contrib = round(neg_component, 3)
    factors.append({
        "factor": "negative sentiment",
        "weight": neg_contrib
    })
    score += neg_contrib

    # 4. Urgency Flag (10% weight)
    urg_contrib = round(urgency * 0.10, 3)
    score += urg_contrib
    if urgency > 0:
        factors.append({
            "factor": "urgent wording",
            "weight": urg_contrib
        })

    # 5. Complaint Aging Multiplier (if unresolved > 24 hours)
    if complaint_age_hours > 24 and status.lower() not in ("closed", "resolved"):
        aging_boost = min(0.15, round((complaint_age_hours / 48) * 0.05, 3))
        score += aging_boost
        factors.append({
            "factor": f"unresolved duration ({round(complaint_age_hours)}h)",
            "weight": aging_boost
        })

    final_score = round(min(1.0, max(0.10, score)), 3)
    tier = priority_tier(final_score)
    p_label = priority_label(final_score)

    reason_parts = [f"{f['factor']} (+{f['weight']})" for f in factors if f['weight'] > 0]
    priority_reason = ", ".join(reason_parts) if reason_parts else "Standard baseline priority"

    return tier, final_score, p_label, priority_reason, factors


# Semantic alias matching legacy interface
def score_priority(category: str, sentiment: float, urgency: int, risk: float,
                   risk_factors: list) -> Tuple[float, list]:
    """Legacy compatibility adapter returning (priority_score, priority_factors)."""
    _tier, score, _label, _reason, factors = calculate_priority(
        category=category,
        sentiment_score=sentiment,
        urgency=urgency,
        escalation_risk_score=risk,
        escalation_factors=risk_factors
    )
    return score, factors
