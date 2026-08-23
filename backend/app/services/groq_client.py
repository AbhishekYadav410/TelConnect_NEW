"""Groq LLM & Whisper wrapper — the primary AI integration in the stack (free tier).

Reads GROQ_API_KEY from the environment or backend/.env. Every call has a
deterministic offline fallback so the whole platform runs (and tests pass)
with no key and no network. Responses are cached in-process to stay inside
free-tier rate limits.
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "groq/compound",
    "groq/compound-mini",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

_cache: dict[str, str] = {}
_active_model: str | None = None


def _load_env_file() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(base_dir)
    for path in (
        os.path.join(base_dir, ".env"),
        os.path.join(root_dir, ".env"),
        os.path.join(base_dir, ".env.local"),
        os.path.join(root_dir, ".env.local"),
    ):
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)


_load_env_file()


def api_key() -> str | None:
    return os.environ.get("GROQ_API_KEY") or None


def groq_available() -> bool:
    return api_key() is not None


def get_model() -> str:
    global _active_model
    if _active_model:
        return _active_model
    env_model = os.environ.get("GROQ_MODEL")
    return env_model if env_model else DEFAULT_MODELS[0]


def _hash_messages(messages: list[dict], max_tokens: int, temperature: float) -> str:
    raw = json.dumps({"m": messages, "tok": max_tokens, "temp": temperature}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _clean_llm_text(text: str) -> str:
    """Strip internal reasoning tags, think blocks, and normalize unicode."""
    if "<think>" in text and "</think>" in text:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # Clean possible markdown reasoning headings if present
    if "**Reasoning**" in text and "**Answer**" in text:
        text = text.split("**Answer**")[-1].strip()
    elif "### Reasoning" in text and "### Response" in text:
        text = text.split("### Response")[-1].strip()

    # Normalize unicode hyphens/quotes/spaces
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212\ufe63\uff0d]", "-", text)
    text = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", text)
    text = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', text)
    text = re.sub(r"[\u202f\u00a0]", " ", text)
    return text.strip()


def groq_chat_messages(messages: list[dict], fallback: str, max_tokens: int = 500,
                       temperature: float = 0.3) -> str:
    """Chat completion with a full list of messages. Any failure returns fallback."""
    global _active_model
    if not groq_available():
        return fallback
    cache_key = _hash_messages(messages, max_tokens, temperature)
    if cache_key in _cache:
        return _cache[cache_key]

    models_to_try = []
    current = get_model()
    if current:
        models_to_try.append(current)
    for m in DEFAULT_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    for model in models_to_try:
        body = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }).encode()
        req = urllib.request.Request(
            GROQ_URL, data=body,
            headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json", "User-Agent": "TCI-Assistant/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read())
            raw_content = (data["choices"][0]["message"].get("content") or "").strip()
            text = _clean_llm_text(raw_content)
            if not text:
                continue
            _cache[cache_key] = text
            _active_model = model
            return text
        except urllib.error.HTTPError as he:
            if he.code in (400, 404):
                continue
            return fallback
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError, OSError):
            return fallback
    return fallback


def groq_chat(system: str, user: str, fallback: str, max_tokens: int = 500,
              temperature: float = 0.3) -> str:
    """One chat completion (system + user). Any failure returns fallback."""
    return groq_chat_messages(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        fallback=fallback, max_tokens=max_tokens, temperature=temperature
    )


def groq_json_messages(messages: list[dict], fallback, max_tokens: int = 600):
    """Chat completion expected to return JSON from messages; parses defensively."""
    raw = groq_chat_messages(messages, fallback="", max_tokens=max_tokens, temperature=0.1)
    if not raw:
        return fallback
    match = re.search(r"\{.*\}|\[.*\]", raw, re.DOTALL)
    if not match:
        return fallback
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return fallback


def groq_json(system: str, user: str, fallback, max_tokens: int = 600):
    """Chat completion expected to return JSON; parses defensively."""
    return groq_json_messages(
        [{"role": "system", "content": system + " Respond with ONLY valid JSON, no prose."},
         {"role": "user", "content": user}],
        fallback=fallback, max_tokens=max_tokens
    )


WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = os.environ.get("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> str | None:
    """Voice-to-text via Groq Whisper with multilingual support (English, Hindi, Hinglish).

    Accepts language code (e.g. 'hi', 'en') and contextual prompt hints.
    """
    if not groq_available():
        return None
    boundary = "----tciboundary" + os.urandom(8).hex()
    parts = []
    fields = [("model", WHISPER_MODEL), ("response_format", "text")]

    if language and language in ("hi", "en"):
        fields.append(("language", language))

    default_prompt = prompt or "Indian telecom customer support query in Hindi, Hinglish, or English. Broadband, Wi-Fi, recharge, network speed, ticket status."
    fields.append(("prompt", default_prompt))

    for name, value in fields:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())

    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n".encode() + audio_bytes + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(WHISPER_URL, data=body, headers={
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode().strip()
            return text
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None
