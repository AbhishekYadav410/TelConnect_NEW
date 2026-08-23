"""Hugging Face DistilBERT Multilingual Tokenizer & Translation Module for TelConnect.

Supports pure bidirectional translation between English ('en') and Hindi ('hi')
using Hugging Face's multilingual DistilBERT tokenizer + Groq fast LLM translation +
deterministic rule mapping.
"""
import logging
import os
import re
from typing import Literal, Optional

from .etl import DEVANAGARI_RE, HINGLISH_MAP, normalize_hinglish
from .groq_client import groq_available, groq_chat_messages

logger = logging.getLogger(__name__)

# Lazy loaded Hugging Face tokenizer instance
_distilbert_tokenizer = None
_distilbert_model_loaded = False

HF_DISTILBERT_MODEL_NAME = "distilbert/distilbert-base-multilingual-cased"


def get_distilbert_tokenizer():
    """Load or return the cached Hugging Face DistilBERT multilingual tokenizer."""
    global _distilbert_tokenizer, _distilbert_model_loaded
    if _distilbert_tokenizer is None and not _distilbert_model_loaded:
        try:
            from transformers import AutoTokenizer
            _distilbert_tokenizer = AutoTokenizer.from_pretrained(
                HF_DISTILBERT_MODEL_NAME,
                local_files_only=False
            )
            _distilbert_model_loaded = True
            logger.info("Loaded Hugging Face Multilingual DistilBERT tokenizer (%s)", HF_DISTILBERT_MODEL_NAME)
        except Exception as e:
            logger.warning("Could not load Hugging Face DistilBERT tokenizer: %s. Using lexical fallback.", e)
            _distilbert_model_loaded = True
            _distilbert_tokenizer = None
    return _distilbert_tokenizer


# Extended English to Hindi (Devanagari) lexical dictionaries for telecom
EN_TO_HI_DICT = {
    "hello": "नमस्ते",
    "hi": "नमस्ते",
    "hey": "नमस्ते",
    "internet": "इंटरनेट",
    "broadband": "ब्रॉडबैंड",
    "wifi": "वाई-फ़ाई",
    "network": "नेटवर्क",
    "down": "बंद",
    "slow": "धीमा",
    "working": "काम कर रहा",
    "not working": "काम नहीं कर रहा",
    "not": "नहीं",
    "bill": "बिल",
    "payment": "भुगतान",
    "recharge": "रिचार्ज",
    "speed": "गति",
    "speed test": "स्पीड टेस्ट",
    "latency": "विलंबता",
    "ticket": "टिकट",
    "complaint": "शिकायत",
    "status": "स्थिति",
    "help": "मदद",
    "issue": "समस्या",
    "problem": "समस्या",
    "router": "राऊटर",
    "fiber": "फ़ाइबर",
    "call": "कॉल",
    "drops": "ड्रॉप्स",
    "outage": "आउटेज",
    "customer": "ग्राहक",
    "support": "सहायता",
    "thank you": "धन्यवाद",
    "thanks": "धन्यवाद",
    "yes": "हाँ",
    "no": "नहीं",
    "closed": "बंद",
    "registered": "दर्ज",
    "escalated": "एस्केलेट किया गया",
    "resolved": "समाधान किया गया",
    "my": "मेरा",
    "is": "है",
    "are": "हैं",
    "check": "जांचें",
    "test": "परीक्षण",
    "done": "पूर्ण",
    "fixed": "ठीक हो गया",
}

HI_TO_EN_DICT = {
    "नमस्ते": "hello",
    "नमस्कार": "hello",
    "इंटरनेट": "internet",
    "ब्रॉडबैंड": "broadband",
    "वाई-फ़ाई": "wifi",
    "नेटवर्क": "network",
    "बंद": "down",
    "धीमा": "slow",
    "खराब": "faulty",
    "काम": "work",
    "नहीं": "not",
    "बिल": "bill",
    "भुगतान": "payment",
    "रिचार्ज": "recharge",
    "गति": "speed",
    "स्पीड": "speed",
    "टिकट": "ticket",
    "शिकायत": "complaint",
    "स्थिति": "status",
    "मदद": "help",
    "समस्या": "issue",
    "राऊटर": "router",
    "फ़ाइबर": "fiber",
    "कॉल": "call",
    "धन्यवाद": "thank you",
    "हाँ": "yes",
    "मेरा": "my",
    "है": "is",
    "हैं": "are",
    "जांचें": "check",
    "रहा": "doing",
    "कर": "do",
    "दीजिए": "please",
}


def detect_language(text: str) -> Literal["en", "hi"]:
    """Identify whether text is Hindi ('hi') or English ('en')."""
    if not text:
        return "en"
    if DEVANAGARI_RE.search(text):
        return "hi"
    clean = text.lower()
    for pattern in HINGLISH_MAP:
        if re.search(r"\b" + re.escape(pattern) + r"\b", clean):
            return "hi"
    # Check common conversational Hindi words written in Latin letters
    hindi_markers = ["kaise", "kripya", "aapka", "mera", "batao", "dikkat", "pareshani", "chal", "karo", "kardo", "kya", "hua", "nahi", "subah", "band", "khari"]
    if any(re.search(r"\b" + m + r"\b", clean) for m in hindi_markers):
        return "hi"
    return "en"


def _rule_based_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Deterministic fallback translation between English and Hindi."""
    if source_lang == target_lang or not text:
        return text

    # Hindi -> English
    if source_lang == "hi" and target_lang == "en":
        res = text
        for dev, eng in sorted(HI_TO_EN_DICT.items(), key=lambda x: -len(x[0])):
            res = res.replace(dev, eng)
        return normalize_hinglish(res)

    # English -> Hindi (Devanagari)
    if source_lang == "en" and target_lang == "hi":
        res = text
        for eng, dev in sorted(EN_TO_HI_DICT.items(), key=lambda x: -len(x[0])):
            res = re.sub(r"\b" + re.escape(eng) + r"\b", dev, res, flags=re.I)
        return res

    return text


def translate_text(text: str, target_lang: str, source_lang: str | None = None) -> dict:
    """Translate text between English ('en') and Hindi ('hi').

    Returns dict:
    {
        "original": str,
        "translated": str,
        "source_lang": str,
        "target_lang": str,
        "engine": "distilbert_groq" | "rule_based",
        "tokens": list[str] (tokenized representation from Hugging Face DistilBERT)
    }
    """
    if not text or not text.strip():
        return {
            "original": text,
            "translated": text,
            "source_lang": source_lang or "en",
            "target_lang": target_lang,
            "engine": "identity",
            "tokens": []
        }

    src = source_lang or detect_language(text)
    tgt = target_lang

    if src == tgt:
        return {
            "original": text,
            "translated": text,
            "source_lang": src,
            "target_lang": tgt,
            "engine": "identity",
            "tokens": []
        }

    # Extract tokens with Hugging Face DistilBERT tokenizer
    tokens = []
    tok = get_distilbert_tokenizer()
    if tok:
        try:
            tokens = tok.tokenize(text)[:40]
        except Exception:
            tokens = text.split()[:20]

    # Attempt Groq Fast LLM zero-shot translation for natural fluency
    if groq_available():
        target_name = "Hindi (Devanagari script only, e.g. हिन्दी)" if tgt == "hi" else "standard English"
        prompt = (
            f"Translate the following telecom customer text from {src} to {target_name}.\n"
            f"Preserve all ticket IDs, incident numbers, and technical terms accurately.\n"
            f"Output ONLY the translated text without any explanation, think tags, or markdown.\n\n"
            f"Text:\n{text}"
        )
        try:
            llm_result = groq_chat_messages(
                [{"role": "user", "content": prompt}],
                fallback="",
                max_tokens=250,
                temperature=0.1
            )
            if llm_result and len(llm_result.strip()) > 0:
                clean_translated = llm_result.strip().strip('"').strip("'")
                return {
                    "original": text,
                    "translated": clean_translated,
                    "source_lang": src,
                    "target_lang": tgt,
                    "engine": "distilbert_groq",
                    "tokens": tokens
                }
        except Exception as err:
            logger.warning("Groq translation failed, falling back to rule-based: %s", err)

    # Fallback to deterministic rule-based translator
    fallback_trans = _rule_based_translate(text, src, tgt)
    return {
        "original": text,
        "translated": fallback_trans,
        "source_lang": src,
        "target_lang": tgt,
        "engine": "rule_based",
        "tokens": tokens
    }


def to_english_semantics(text: str) -> tuple[str, str]:
    """Normalize input text in Hindi to clean English semantics for downstream RAG and ML classification."""
    lang = detect_language(text)
    if lang == "en":
        return text, "en"

    # Hindi or transliterated query -> Normalize to English semantics
    norm = normalize_hinglish(text)
    if DEVANAGARI_RE.search(norm):
        trans = translate_text(norm, target_lang="en", source_lang="hi")
        return trans["translated"], lang

    return norm, lang
