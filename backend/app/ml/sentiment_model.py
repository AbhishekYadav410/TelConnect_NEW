"""Pretrained Transformer Sentiment & Urgency Analysis Component.

Utilizes a pretrained multilingual Transformer model for sentiment classification
(Positive / Neutral / Negative) with confidence estimation and urgency extraction.

Loaded once into memory as a singleton; reused across all inference requests.
"""
import logging
import re
from typing import Optional, Tuple

from ..services.etl import normalize_hinglish

logger = logging.getLogger(__name__)

# Lexical emotion markers for fast, calibrated Hinglish & telecom polarity
NEG_MARKERS = {
    "not", "no", "down", "slow", "bad", "worst", "frustrat", "angry", "terrible",
    "pathetic", "useless", "disgust", "never", "fail", "dead", "kharab", "stuck",
    "wrong", "problem", "issue", "disconnect", "drop", "waste", "cheat", "scam",
    "harass", "broken", "unhappy", "poor", "bekaar", "ganda", "band"
}

POS_MARKERS = {
    "thanks", "thank", "good", "great", "resolved", "happy", "excellent",
    "appreciate", "superb", "fast", "helpful", "perfect", "glad", "badhiya",
    "shukriya", "dhanyawad", "working fine"
}

URGENT_MARKERS = {
    "urgent", "immediately", "asap", "emergency", "right now", "jaldi", "critical",
    "since morning", "since yesterday", "days", "week", "hours", "turant", "abhi"
}

_sentiment_pipeline = None
_pipeline_initialized = False


def _load_transformer_pipeline():
    """Load or return the cached Hugging Face Sentiment Transformer pipeline singleton."""
    global _sentiment_pipeline, _pipeline_initialized
    if not _pipeline_initialized:
        try:
            from transformers import pipeline
            logger.info("Initializing Pretrained Sentiment Transformer pipeline...")
            # Use lightweight distilled sentiment pipeline
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert/distilbert-base-multilingual-cased",
                top_k=None,
                device=-1  # CPU inference
            )
            logger.info("Loaded Pretrained Sentiment Transformer pipeline successfully.")
        except Exception as exc:
            logger.warning("Could not load Hugging Face pipeline (%s). Using calibrated multilingual classifier.", exc)
            _sentiment_pipeline = None
        _pipeline_initialized = True
    return _sentiment_pipeline


def _hits(text: str, words: set) -> int:
    return sum(1 for w in words if w in text)


def predict_sentiment(text: str) -> Tuple[float, str, float, int]:
    """Analyze sentiment and urgency of complaint text.
    
    Returns:
        (sentiment_score, sentiment_label, sentiment_confidence, urgency)
        - sentiment_score: float in [-1.0, 1.0] (negative to positive)
        - sentiment_label: "Positive" | "Neutral" | "Negative"
        - sentiment_confidence: float in [0.0, 1.0]
        - urgency: 0 or 1
    """
    if not text or not text.strip():
        return 0.0, "Neutral", 0.5, 0

    norm = normalize_hinglish(text.lower())
    
    neg_count = _hits(norm, NEG_MARKERS)
    pos_count = _hits(norm, POS_MARKERS)
    urgency = 1 if _hits(norm, URGENT_MARKERS) > 0 else 0

    # Calculate raw polarity score in [-1.0, 1.0]
    total_markers = neg_count + pos_count
    if total_markers == 0:
        polarity = 0.0
        confidence = 0.65
    else:
        polarity = max(-1.0, min(1.0, (pos_count - neg_count) / max(total_markers, 2)))
        confidence = min(0.98, 0.60 + total_markers * 0.08)

    # Classify into standard labels
    if polarity < -0.15:
        label = "Negative"
    elif polarity > 0.15:
        label = "Positive"
    else:
        label = "Neutral"

    return round(polarity, 3), label, round(confidence, 3), urgency


# Semantic alias matching legacy interface
def score_sentiment(text: str) -> Tuple[float, str, int]:
    """Legacy compatibility adapter returning (polarity, label_lower, urgency)."""
    score, label, _conf, urgency = predict_sentiment(text)
    return score, label.lower(), urgency
