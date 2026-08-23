"""Modular ML Layer Package for TelConnect.

Exposes unified public interfaces while preserving clean separation of concerns:
- category_model: TF-IDF + Logistic Regression
- sentiment_model: Pretrained Transformer
- priority_model: Multi-factor explainable priority engine
- escalation: Status-aware escalation risk engine
- ml_service: Central orchestration
- train_category: Offline training script
"""
from .category_model import (
    CATEGORIES,
    classify_category,
    explain_category_reasoning,
    format_category_reasoning_response,
    get_metrics,
    predict_categories,
    predict_category,
    predict_multilabel,
)
from .escalation import (
    predict_escalation,
    score_escalation_risk,
)
from .ml_service import (
    analyze_complaint,
    score_complaint_row,
    score_unscored,
    ticket_summary,
)
from .priority_model import (
    calculate_priority,
    priority_label,
    priority_tier,
    score_priority,
    sla_deadline_for,
)
from .sentiment_model import (
    predict_sentiment,
    score_sentiment,
)
from .train_category import train_and_save

# Legacy compatibility aliases
metrics = get_metrics
train = train_and_save

__all__ = [
    "CATEGORIES",
    "analyze_complaint",
    "calculate_priority",
    "classify_category",
    "explain_category_reasoning",
    "format_category_reasoning_response",
    "get_metrics",
    "metrics",
    "predict_categories",
    "predict_category",
    "predict_multilabel",
    "predict_escalation",
    "predict_sentiment",
    "priority_label",
    "priority_tier",
    "score_complaint_row",
    "score_escalation_risk",
    "score_priority",
    "score_sentiment",
    "score_unscored",
    "sla_deadline_for",
    "ticket_summary",
    "train",
    "train_and_save",
]
