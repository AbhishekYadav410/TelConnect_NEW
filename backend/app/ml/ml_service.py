"""Central ML Orchestration Service.

Provides unified entry points for single and batch complaint analysis,
orchestrating Category, Sentiment, Escalation, and Priority models.

Model-specific logic resides entirely in the respective component modules.
"""
import json
import logging
import os
from typing import Any, Dict, Optional

from .. import db
from ..services.groq_client import groq_chat
from .category_model import predict_category
from .escalation import predict_escalation
from .priority_model import calculate_priority, priority_label, sla_deadline_for
from .sentiment_model import predict_sentiment

logger = logging.getLogger(__name__)


def ticket_summary(
    text: str,
    category: str,
    region: str,
    status: str,
    use_llm: bool = False
) -> str:
    """Generate a concise one-sentence plain language summary of the ticket."""
    clean_text = text[:90] + ("..." if len(text) > 90 else "")
    fallback = f"{category.capitalize()} complaint reported in {region}: \"{clean_text}\""
    
    if not use_llm:
        return fallback

    try:
        summary = groq_chat(
            system="You summarise telecom complaints. Return ONE plain-language sentence (max 25 words) "
                   "stating the issue and the area. Do NOT mention status. No preamble.",
            user=f"Complaint: {text}\nCategory: {category}\nRegion: {region}\nStatus: {status}",
            fallback=fallback,
            max_tokens=150
        )
        return summary if summary and summary.strip() else fallback
    except Exception as exc:
        logger.warning("Groq ticket summary exception (%s). Using template summary.", exc)
        return fallback


def analyze_complaint(
    text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Orchestrate all ML models on a single complaint text and metadata.
    
    Returns:
        Standardized dictionary containing all ML predictions, confidence scores,
        risk tiers, explainability reasons, and ticket summaries.
    """
    metadata = metadata or {}
    status = str(metadata.get("status", "open"))
    region = str(metadata.get("region", "Unknown"))
    created_iso = metadata.get("timestamp") or db.now_iso()
    use_llm_summary = bool(metadata.get("use_llm_summary", False))
    repeat_count = int(metadata.get("repeat_count", 0))
    complaint_age_hours = float(metadata.get("complaint_age_hours", 0.0))

    # 1. Category Prediction
    category, cat_conf = predict_category(text)

    # 2. Sentiment & Urgency Prediction
    sent_score, sent_label, sent_conf, urgency = predict_sentiment(text)

    # 3. Escalation Risk Assessment
    esc_tier, esc_score, esc_reason, esc_factors = predict_escalation(
        text=text,
        sentiment_score=sent_score,
        urgency=urgency,
        status=status,
        repeat_count=repeat_count
    )

    # 4. Priority & SLA Calculation
    prio_tier, prio_score, prio_lbl, prio_reason, prio_factors = calculate_priority(
        category=category,
        sentiment_score=sent_score,
        urgency=urgency,
        escalation_risk_score=esc_score,
        escalation_factors=esc_factors,
        category_confidence=cat_conf,
        complaint_age_hours=complaint_age_hours,
        status=status
    )

    # 5. Ticket Summary
    summary = ticket_summary(
        text=text,
        category=category,
        region=region,
        status=status,
        use_llm=use_llm_summary
    )

    sla_deadline = sla_deadline_for(prio_score, created_iso)

    return {
        "category": category,
        "category_confidence": cat_conf,
        "sentiment": sent_score,
        "sentiment_label": sent_label,
        "sentiment_confidence": sent_conf,
        "urgency": urgency,
        "priority": prio_tier,
        "priority_score": prio_score,
        "priority_label": prio_lbl,
        "priority_reason": prio_reason,
        "priority_factors": json.dumps(prio_factors),
        "escalation_risk": esc_score,
        "escalation_risk_label": esc_tier,
        "escalation_reason": esc_reason,
        "ticket_summary": summary,
        "sla_deadline": sla_deadline
    }


def score_complaint_row(complaint: dict, use_llm_summary: bool = False) -> dict:
    """Score a single complaint dictionary representation from DB."""
    text = complaint.get("text", "")
    metadata = {
        "status": complaint.get("status", "open"),
        "region": complaint.get("region", "Unknown"),
        "timestamp": complaint.get("timestamp"),
        "use_llm_summary": use_llm_summary
    }
    result = analyze_complaint(text, metadata)
    return {
        "category": result["category"],
        "category_confidence": result["category_confidence"],
        "sentiment": result["sentiment"],
        "sentiment_label": result["sentiment_label"].lower(),
        "sentiment_confidence": result["sentiment_confidence"],
        "urgency": result["urgency"],
        "escalation_risk": result["escalation_risk"],
        "escalation_reason": result["escalation_reason"],
        "priority_score": result["priority_score"],
        "priority_label": result["priority_label"],
        "priority_reason": result["priority_reason"],
        "priority_factors": result["priority_factors"],
        "ticket_summary": result["ticket_summary"],
        "sla_deadline": result["sla_deadline"]
    }


def score_unscored(limit: int = 5000) -> int:
    """Batch-score complaints with missing category or priority.
    
    Called after CSV upload and background scheduler tick.
    Uses preloaded models without retraining.
    """
    conn = db.connect()
    rows = conn.execute(
        "SELECT complaint_id, text, region, status, timestamp FROM complaints "
        "WHERE category IS NULL LIMIT ?", (limit,)).fetchall()
    
    if not rows:
        return 0

    for row in rows:
        upd = score_complaint_row(dict(row), use_llm_summary=False)
        conn.execute(
            "UPDATE complaints SET category=?, sentiment=?, sentiment_label=?, urgency=?, "
            "escalation_risk=?, priority_score=?, priority_factors=?, ticket_summary=?, "
            "priority_label=?, sla_deadline=? WHERE complaint_id=?",
            (upd["category"], upd["sentiment"], upd["sentiment_label"], upd["urgency"],
             upd["escalation_risk"], upd["priority_score"], upd["priority_factors"],
             upd["ticket_summary"], upd["priority_label"],
             upd["sla_deadline"],
             row["complaint_id"])
        )
    conn.commit()
    logger.info("Batch scored %d complaints successfully.", len(rows))
    return len(rows)
