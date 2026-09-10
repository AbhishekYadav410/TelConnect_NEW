"""Lightweight, High-Performance Sentiment & Urgency Analysis Component.

Replaces heavy transformer models with a fast, zero-memory, rule-and-lexicon
sentiment engine (VADER / TextBlob style) optimized specifically for telecom
complaints and multi-lingual English, Hindi (Devanagari), and Hinglish expressions.

Designed for high-throughput, low-memory production environments (such as Railway
512MB free tier containers) with 0 MB model footprint and sub-millisecond execution.

Returns:
    sentiment_score      -> [-1.0, 1.0] (continuous polarity)
    sentiment_label      -> Positive / Neutral / Negative
    sentiment_confidence -> [0.0, 1.0]
    urgency              -> 0 / 1
"""

import logging
import re
from typing import Tuple

from ..services.etl import normalize_hinglish

logger = logging.getLogger(__name__)

SENTIMENT_MODEL = "lightweight-telecom-lexicon-engine"

# Cached pipeline reference for backward compatibility
_sentiment_pipeline = None
_pipeline_initialized = True


# ---------------------------------------------------------------------------
# Telecom-specific urgency markers
# ---------------------------------------------------------------------------

URGENT_MARKERS = {
    "urgent",
    "urgently",
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
    "loss",
    "danger",
    "trai",
    "court",
    "legal",
}


# ---------------------------------------------------------------------------
# Lexicon Dictionaries (English, Hinglish & Devanagari)
# ---------------------------------------------------------------------------

# Strong Negative Terms (Weight -1.0)
STRONG_NEGATIVES = {
    "terrible", "horrible", "worst", "pathetic", "disgusting", "useless", "disaster",
    "fraud", "scam", "cheat", "cheated", "loot", "harass", "harassment", "furious",
    "unacceptable", "hopeless", "outrageous", "ridiculous", "rubbish", "bakwaas",
    "lootna", "dhokha", "ghatiya", "barbaad", "third class",
}

# Standard Negative Terms (Weight -0.6)
NEGATIVE_TERMS = {
    "not working", "no signal", "down", "slow", "bad", "angry", "frustrat", "frustrated",
    "frustrating", "dead", "fail", "failed", "failing", "failure", "stuck", "broken",
    "problem", "problems", "issue", "issues", "disconnect", "disconnected", "disconnecting",
    "drop", "drops", "dropping", "poor", "unhappy", "waste", "trouble", "error", "fault",
    "cut", "cutting", "interrupted", "buffering", "delay", "delayed", "glitch",
    "kharab", "bekaar", "band", "nahi chal raha", "kaam nahi", "pareshan", "pareshani",
    "slow net", "net nahi", "call drop", "red light", "loss", "ganda", "dikkat",
    "खराब", "बंद", "धीमा", "समस्या", "परेशानी", "कट गया", "काम नहीं",
}

# Strong Positive Terms (Weight +1.0)
STRONG_POSITIVES = {
    "excellent", "outstanding", "perfect", "fantastic", "amazing", "wonderful",
    "superb", "brilliant", "delighted", "kudos", "shandar", "zabardast", "lajawab",
}

# Standard Positive Terms (Weight +0.6)
POSITIVE_TERMS = {
    "thanks", "thank", "thank you", "good", "great", "resolved", "happy", "fast",
    "speedy", "appreciate", "helpful", "fixed", "restored", "stable", "smooth",
    "satisfied", "satisfaction", "glad", "working fine", "works great", "speed good",
    "badhiya", "shukriya", "dhanyawad", "theek", "theek hai", "chal gaya", "kaam kar raha",
    "achha", "bahut achha", "bahut badhiya",
    "धन्यवाद", "शुक्रिया", "अच्छा", "बढ़िया", "संतुष्ट", "ठीक है",
}

# Negation words that flip polarity of trailing tokens
NEGATION_WORDS = {
    "not", "no", "never", "none", "neither", "nor", "hardly", "barely",
    "nahi", "nahin", "na", "mat", "bina",
}

# Intensifiers that boost magnitude
INTENSIFIERS = {
    "very", "extremely", "super", "really", "completely", "totally", "too",
    "bahut", "bohot", "ekdum", "zyada", "jyada",
}


# ---------------------------------------------------------------------------
# Urgency Detection
# ---------------------------------------------------------------------------

def _detect_urgency(text: str) -> int:
    """Return 1 if text contains an urgency signal, else 0."""
    t_lower = text.lower()
    for marker in URGENT_MARKERS:
        if marker in t_lower:
            return 1
    return 0


# ---------------------------------------------------------------------------
# Core Sentiment Analysis
# ---------------------------------------------------------------------------

def predict_sentiment(
    text: str,
) -> Tuple[float, str, float, int]:
    """Analyze sentiment and urgency of complaint text using calibrated lexicon rules.

    Zero-memory footprint, sub-millisecond latency, and fully offline compatible.

    Returns:
        (sentiment_score, sentiment_label, sentiment_confidence, urgency)
        - sentiment_score: float in [-1.0, 1.0] (continuous score)
        - sentiment_label: "Positive" | "Neutral" | "Negative"
        - sentiment_confidence: float in [0.0, 1.0]
        - urgency: 0 or 1
    """
    if not text or not text.strip():
        return (0.0, "Neutral", 0.5, 0)

    # Normalize Hinglish, transliteration, and lowercasing
    norm = normalize_hinglish(text.lower().strip())
    urgency = _detect_urgency(norm)

    tokens = re.findall(r"\b\w+\b", norm)
    if not tokens:
        return (0.0, "Neutral", 0.5, urgency)

    pos_score = 0.0
    neg_score = 0.0
    total_signals = 0

    # 1. Multi-word phrase matching
    for phrase in STRONG_NEGATIVES:
        if " " in phrase and phrase in norm:
            neg_score += 1.0
            total_signals += 1
    for phrase in NEGATIVE_TERMS:
        if " " in phrase and phrase in norm:
            neg_score += 0.6
            total_signals += 1

    for phrase in STRONG_POSITIVES:
        if " " in phrase and phrase in norm:
            pos_score += 1.0
            total_signals += 1
    for phrase in POSITIVE_TERMS:
        if " " in phrase and phrase in norm:
            pos_score += 0.6
            total_signals += 1

    # 2. Token-level analysis with negation and intensifier windows
    n = len(tokens)
    for i, token in enumerate(tokens):
        # Look behind for negation up to 2 tokens
        is_negated = False
        start_idx = max(0, i - 2)
        for prev in tokens[start_idx:i]:
            if prev in NEGATION_WORDS:
                is_negated = True
                break

        # Look behind for intensifier
        multiplier = 1.0
        if i > 0 and tokens[i - 1] in INTENSIFIERS:
            multiplier = 1.35

        # Check negative lexicon
        if token in STRONG_NEGATIVES:
            weight = 1.0 * multiplier
            if is_negated:
                pos_score += weight * 0.5
            else:
                neg_score += weight
            total_signals += 1
        elif token in NEGATIVE_TERMS:
            weight = 0.6 * multiplier
            if is_negated:
                pos_score += weight * 0.5
            else:
                neg_score += weight
            total_signals += 1

        # Check positive lexicon
        elif token in STRONG_POSITIVES:
            weight = 1.0 * multiplier
            if is_negated:
                neg_score += weight * 0.8
            else:
                pos_score += weight
            total_signals += 1
        elif token in POSITIVE_TERMS:
            weight = 0.6 * multiplier
            if is_negated:
                neg_score += weight * 0.8
            else:
                pos_score += weight
            total_signals += 1

    # 3. Calculate continuous normalized score in [-1.0, 1.0]
    if total_signals == 0:
        score = 0.0
        confidence = 0.65
        label = "Neutral"
    else:
        diff = pos_score - neg_score
        scale = max(pos_score + neg_score, 1.2)
        raw_score = diff / scale
        score = max(-1.0, min(1.0, raw_score))

        # Determine label and confidence
        if score < -0.15:
            label = "Negative"
            confidence = min(0.98, 0.65 + (neg_score / (pos_score + neg_score + 1e-5)) * 0.30)
        elif score > 0.15:
            label = "Positive"
            confidence = min(0.98, 0.65 + (pos_score / (pos_score + neg_score + 1e-5)) * 0.30)
        else:
            label = "Neutral"
            confidence = 0.70

    return (
        round(score, 3),
        label,
        round(confidence, 3),
        urgency,
    )


# ---------------------------------------------------------------------------
# Legacy compatibility
# ---------------------------------------------------------------------------

def score_sentiment(
    text: str,
) -> Tuple[float, str, int]:
    """Legacy interface returning (score, label_lowercase, urgency)."""
    score, label, _confidence, urgency = predict_sentiment(text)
    return (
        score,
        label.lower(),
        urgency,
    )