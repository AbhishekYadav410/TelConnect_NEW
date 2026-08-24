"""Pretrained Transformer Sentiment & Urgency Analysis Component.

Uses a multilingual DistilBERT sentiment model to classify complaint text
as Positive, Neutral, or Negative.

The model is pretrained and sentiment-fine-tuned; the TelConnect complaint
dataset is NOT used to train this sentiment model.

Urgency remains a deterministic telecom-specific rule because urgency is
different from sentiment.

Returns:
    sentiment_score      -> [-1.0, 1.0]
    sentiment_label      -> Positive / Neutral / Negative
    sentiment_confidence -> [0.0, 1.0]
    urgency              -> 0 / 1
"""

import logging
from typing import Tuple

from ..services.etl import normalize_hinglish

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telecom-specific urgency markers
# ---------------------------------------------------------------------------

URGENT_MARKERS = {
    "urgent",
    "immediately",
    "asap",
    "emergency",
    "right now",
    "jaldi",
    "critical",
    "since morning",
    "since yesterday",
    "days",
    "week",
    "hours",
    "turant",
    "abhi",
}


# ---------------------------------------------------------------------------
# Cached Transformer model
# ---------------------------------------------------------------------------

_sentiment_pipeline = None
_pipeline_initialized = False


SENTIMENT_MODEL = (
    "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
)


def _load_transformer_pipeline():
    """Load the sentiment model once and reuse it."""

    global _sentiment_pipeline, _pipeline_initialized

    if _pipeline_initialized:
        return _sentiment_pipeline

    try:
        from transformers import pipeline

        logger.info(
            "Initializing multilingual DistilBERT sentiment model..."
        )

        _sentiment_pipeline = pipeline(
            "text-classification",
            model=SENTIMENT_MODEL,
            tokenizer=SENTIMENT_MODEL,
            top_k=None,
            device=-1,  # CPU
        )

        logger.info(
            "Multilingual DistilBERT sentiment model loaded successfully."
        )

    except Exception as exc:
        logger.exception(
            "Could not load sentiment model: %s",
            exc
        )
        _sentiment_pipeline = None

    _pipeline_initialized = True

    return _sentiment_pipeline


# ---------------------------------------------------------------------------
# Urgency
# ---------------------------------------------------------------------------

def _detect_urgency(text: str) -> int:
    """Return 1 if the complaint contains an urgency signal."""

    return 1 if any(
        marker in text
        for marker in URGENT_MARKERS
    ) else 0


# ---------------------------------------------------------------------------
# Convert Transformer probabilities into TelConnect score
# ---------------------------------------------------------------------------

def _calculate_sentiment_score(results) -> float:
    """
    Convert model probabilities into TelConnect's [-1, 1] score.

    Negative probability pushes the score toward -1.
    Positive probability pushes the score toward +1.
    Neutral keeps it around 0.

    Example:

        positive = 0.05
        neutral  = 0.10
        negative = 0.85

        score = -0.80
    """

    scores = {
        item["label"].lower(): float(item["score"])
        for item in results
    }

    positive = scores.get("positive", 0.0)
    negative = scores.get("negative", 0.0)

    return max(
        -1.0,
        min(
            1.0,
            positive - negative
        )
    )


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def predict_sentiment(
    text: str
) -> Tuple[float, str, float, int]:
    """
    Analyze complaint sentiment and urgency.

    Returns:

        (
            sentiment_score,
            sentiment_label,
            sentiment_confidence,
            urgency
        )

    sentiment_score:
        -1.0 -> strongly negative
         0.0 -> neutral
        +1.0 -> strongly positive

    sentiment_label:
        Positive / Neutral / Negative

    sentiment_confidence:
        Probability assigned by the Transformer to the winning class.

    urgency:
        0 or 1
    """

    # Empty complaint
    if not text or not text.strip():
        return (
            0.0,
            "Neutral",
            0.5,
            0
        )

    # Normalize English / Hindi / Hinglish text
    norm = normalize_hinglish(text.lower())

    # Urgency is handled separately
    urgency = _detect_urgency(norm)

    # Load/reuse Transformer
    model = _load_transformer_pipeline()

    # Safety fallback if model cannot load
    if model is None:
        logger.warning(
            "Sentiment Transformer unavailable. "
            "Returning Neutral sentiment."
        )

        return (
            0.0,
            "Neutral",
            0.0,
            urgency
        )

    try:
        # Run Transformer inference
        raw_results = model(
            norm,
            truncation=True,
            max_length=512
        )

        # top_k=None normally returns:
        #
        # [
        #   [
        #       {"label": "positive", "score": ...},
        #       {"label": "neutral", "score": ...},
        #       {"label": "negative", "score": ...}
        #   ]
        # ]
        #
        # Handle both possible shapes safely.

        if (
            raw_results
            and isinstance(raw_results[0], list)
        ):
            results = raw_results[0]
        else:
            results = raw_results

        # Find highest-probability class
        best = max(
            results,
            key=lambda item: float(item["score"])
        )

        raw_label = best["label"].lower()
        confidence = float(best["score"])

        # Normalize label
        if raw_label == "negative":
            label = "Negative"

        elif raw_label == "positive":
            label = "Positive"

        elif raw_label == "neutral":
            label = "Neutral"

        else:
            logger.warning(
                "Unexpected sentiment label: %s",
                raw_label
            )

            label = "Neutral"

        # Calculate continuous score
        score = _calculate_sentiment_score(results)

        return (
            round(score, 3),
            label,
            round(confidence, 3),
            urgency
        )

    except Exception as exc:
        logger.exception(
            "Sentiment inference failed: %s",
            exc
        )

        return (
            0.0,
            "Neutral",
            0.0,
            urgency
        )


# ---------------------------------------------------------------------------
# Legacy compatibility
# ---------------------------------------------------------------------------

def score_sentiment(
    text: str
) -> Tuple[float, str, int]:
    """
    Legacy interface.

    Returns:
        sentiment score,
        lowercase label,
        urgency
    """

    score, label, _confidence, urgency = predict_sentiment(text)

    return (
        score,
        label.lower(),
        urgency
    )