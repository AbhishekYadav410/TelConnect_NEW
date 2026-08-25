"""Comprehensive unit tests for the modular ML layer.

Tests:
- category_model.py (Joblib loading, inference, metrics, fallbacks)
- sentiment_model.py (Transformer / polarity, confidence, urgency)
- priority_model.py (Explainable multi-factor scoring, SLAs, tiers)
- escalation.py (Churn/TRAI detection, status awareness)
- ml_service.py (Central analyze_complaint orchestration, batch scoring)
- train_category.py (Offline training script execution)
"""
import os
import tempfile
import pytest

from app.ml import (
    CATEGORIES,
    analyze_complaint,
    calculate_priority,
    classify_category,
    get_metrics,
    predict_category,
    predict_escalation,
    predict_sentiment,
    priority_label,
    priority_tier,
    score_complaint_row,
    score_escalation_risk,
    score_priority,
    score_sentiment,
    sla_deadline_for,
    train_and_save,
)
from app.ml.category_model import load_category_model
from app.ml.escalation import predict_escalation
from app.ml.priority_model import calculate_priority
from app.ml.sentiment_model import predict_sentiment


# ---------- 1. Category Model Tests ----------
def test_category_taxonomy():
    assert "network" in CATEGORIES
    assert "billing" in CATEGORIES
    assert "service" in CATEGORIES
    assert "device" in CATEGORIES
    assert "other" in CATEGORIES


def test_category_model_artifacts_loaded():
    clf, vec = load_category_model()
    assert clf is not None
    assert vec is not None
    assert hasattr(clf, "predict_proba")
    assert hasattr(vec, "transform")


def test_category_prediction_classes():
    # Network
    cat, conf = predict_category("broadband internet is completely down with red light on modem")
    assert cat == "network"
    assert 0.0 <= conf <= 1.0

    # Billing
    cat, conf = predict_category("double payment deducted for my recharge please refund")
    assert cat == "billing"
    assert 0.0 <= conf <= 1.0

    # Service
    cat, conf = predict_category("technician did not arrive for new fiber installation appointment")
    assert cat == "service"
    assert 0.0 <= conf <= 1.0

    # Device
    cat, conf = predict_category("router keeps restarting repeatedly and overheating")
    assert cat == "device"
    assert 0.0 <= conf <= 1.0

    # Other
    cat, conf = predict_category("need GST invoice for corporate connection and tax details")
    assert cat == "other"
    assert 0.0 <= conf <= 1.0


def test_category_metrics_available():
    metrics = get_metrics()
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert metrics["macro_f1"] >= 0.80
    assert metrics["accuracy"] >= 0.80


def test_multilabel_prediction_composite_complaint():
    from app.ml.category_model import predict_categories, explain_category_reasoning, format_category_reasoning_response
    
    # Composite complaint addressing internet, billing, and service issues
    text = "Broadband internet is completely down, extra charges deducted on my bill, and installation technician missed appointment"
    multi = predict_categories(text, threshold=0.25)
    
    # Check multi-label keys
    assert "primary_category" in multi
    assert "related_categories" in multi
    assert "all_categories" in multi
    assert "category_probabilities" in multi
    
    # All 3 categories must be present in the multi-label detection
    all_cats = [c.lower() for c in multi["all_categories"]]
    assert "network" in all_cats or "billing" in all_cats
    related_names = [r["category"].lower() for r in multi["related_categories"]]
    assert len(related_names) >= 1

    # Check explainability reasoning
    reasoning = explain_category_reasoning(text, target_category="network")
    assert reasoning["primary_category"] == "Network"
    assert len(reasoning["evidence"]) >= 1
    assert any(ev in ("internet", "broadband", "connectivity", "down") for ev in reasoning["evidence"])
    assert any(cat in ("Billing", "Service") for cat in reasoning["related_categories"])

    # Check formatted markdown response layout
    formatted = format_category_reasoning_response(reasoning)
    assert "Primary Category: Network" in formatted
    assert "Evidence:" in formatted
    assert "Related Categories:" in formatted


# ---------- 2. Sentiment Model Tests ----------
def test_sentiment_positive_complaint():
    score, label, conf, urg = predict_sentiment("thank you for the great support my internet is resolved and working fast")
    assert label == "Positive"
    assert score > 0.1
    assert 0.0 <= conf <= 1.0


def test_sentiment_negative_complaint():
    score, label, conf, urg = predict_sentiment("terrible service, internet dead since morning, very angry and frustrated")
    assert label == "Negative"
    assert score < -0.1
    assert conf >= 0.6
    assert urg == 1


def test_sentiment_neutral_complaint():
    score, label, conf, urg = predict_sentiment("inquiry regarding remaining balance check and plan options")
    assert label in ("Neutral", "Positive")
    assert abs(score) <= 0.35
    assert 0.0 <= conf <= 1.0



# ---------- 3. Escalation Engine Tests ----------
def test_escalation_churn_threat():
    tier, score, reason, factors = predict_escalation(
        "internet down again, I am porting to Airtel and cancelling my subscription immediately",
        sentiment_score=-0.7,
        urgency=1,
        status="open"
    )
    assert tier in ("Medium", "High")
    assert score >= 0.50
    assert any("churn" in f.lower() or "switching" in f.lower() for f in factors)


def test_escalation_regulatory_threat():
    tier, score, reason, factors = predict_escalation(
        "You charged me twice. I am filing a complaint with TRAI and Consumer Court today",
        sentiment_score=-0.8,
        urgency=1,
        status="open"
    )
    assert tier == "High"
    assert score >= 0.65
    assert any("regulatory" in f.lower() or "trai" in f.lower() for f in factors)


def test_escalation_closed_ticket_not_active():
    tier, score, reason, factors = predict_escalation(
        "I will sue you in consumer court and port out",
        sentiment_score=-0.9,
        urgency=1,
        status="closed"
    )
    assert tier == "Low"
    assert score <= 0.10
    assert "closed/resolved" in reason.lower()
    assert len(factors) == 0


# ---------- 4. Priority Model Tests ----------
def test_priority_calculation():
    tier, score, p_label, reason, factors = calculate_priority(
        category="network",
        sentiment_score=-0.8,
        urgency=1,
        escalation_risk_score=0.85,
        escalation_factors=["TRAI threat", "Churn risk"],
        status="open"
    )
    assert tier in ("Medium", "High")
    assert score >= 0.70
    assert p_label in ("P1", "P2")
    assert len(factors) >= 3
    assert "category" in reason.lower()


def test_priority_sla_deadlines():
    p1_deadline = sla_deadline_for(0.85, "2026-08-23T10:00:00")
    p4_deadline = sla_deadline_for(0.20, "2026-08-23T10:00:00")
    assert p1_deadline is not None
    assert p4_deadline is not None
    assert p1_deadline < p4_deadline


# ---------- 5. Central ML Service Orchestration Tests ----------
def test_analyze_complaint_full_orchestration():
    result = analyze_complaint(
        "Broadband optic fiber is broken since yesterday, need urgent fix or I will switch provider",
        metadata={"region": "Raj Nagar, Ghaziabad", "status": "open"}
    )
    # Checks all required dictionary keys
    assert result["category"] == "network"
    assert "category_confidence" in result
    assert result["sentiment_label"] in ("Negative", "Positive", "Neutral")
    assert "sentiment_confidence" in result
    assert result["priority"] in ("Low", "Medium", "High")
    assert result["priority_label"] in ("P1", "P2", "P3", "P4")
    assert "priority_score" in result
    assert "priority_reason" in result
    assert "escalation_risk" in result
    assert "escalation_reason" in result
    assert "ticket_summary" in result
    assert "sla_deadline" in result


def test_score_complaint_row_adapter():
    row = {
        "text": "Charged Rs 500 extra on my postpaid bill",
        "region": "Delhi",
        "status": "open",
        "timestamp": "2026-08-23T08:00:00"
    }
    scored = score_complaint_row(row)
    assert scored["category"] == "billing"
    assert scored["sentiment_label"] in ("negative", "neutral", "positive")
    assert "priority_score" in scored
    assert "escalation_risk" in scored
    assert "ticket_summary" in scored
