"""Tests for Multilingual DistilBERT translation, LangGraph multi-task agent, and voice endpoints."""
import os
import tempfile

from backend.app.services import translator

os.environ["TCI_DISABLE_SCHEDULER"] = "1"

import pytest
from fastapi.testclient import TestClient

from app import db, seed
from backend.app.routes.main import app, startup_tasks

startup_tasks()
client = TestClient(app)


@pytest.fixture(scope="module")
def tokens():
    admin = client.post("/api/auth/login",
                        json={"email": "admin@telecom.com", "password": "admin123"}).json()
    cust = client.post("/api/auth/login",
                       json={"email": "rohan@example.com", "password": "customer123"}).json()
    return {"admin": {"Authorization": f"Bearer {admin['token']}"},
            "customer": {"Authorization": f"Bearer {cust['token']}"}}


def test_language_detection():
    assert translator.detect_language("मेरा इंटरनेट बंद है") == "hi"
    assert translator.detect_language("net nahi chal raha hai subah se") == "hi"
    assert translator.detect_language("My broadband connection is down") == "en"


def test_translation_engine():
    # Hindi to English
    res_hi = translator.translate_text("मेरा इंटरनेट बंद है", target_lang="en")
    assert "internet" in res_hi["translated"].lower() or "working" in res_hi["translated"].lower() or "down" in res_hi["translated"].lower()

    # English to Hindi
    res_en_hi = translator.translate_text("my internet is not working", target_lang="hi")
    assert any(w in res_en_hi["translated"] for w in ("मेरा", "इंटरनेट", "काम", "नहीं", "बंद"))


def test_translate_api_endpoint(tokens):
    r = client.post("/api/translate", json={
        "text": "mera bill kitna hai",
        "target_lang": "en"
    })
    assert r.status_code == 200
    data = r.json()
    assert "translated" in data
    assert data["target_lang"] == "en"


def test_diagnostic_api_endpoint(tokens):
    r = client.post("/api/chat/diagnostic", headers=tokens["customer"])
    assert r.status_code == 200
    data = r.json()
    assert "download_mbps" in data
    assert "ping_ms" in data
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")


def test_langgraph_speed_test_chat(tokens):
    r = client.post("/api/chat", json={
        "text": "run a speed test and line diagnostic",
        "preferred_language": "en"
    }, headers=tokens["customer"])
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["path"] == "diagnostic"
    assert "diagnostic" in data["meta"]
    assert data["meta"]["diagnostic"]["ping_ms"] > 0
    assert "Mbps" in data["reply"] or "Diagnostic" in data["reply"] or "speed" in data["reply"].lower()


def test_langgraph_hindi_chat(tokens):
    r = client.post("/api/chat", json={
        "text": "नमस्ते, क्या आप मेरी मदद कर सकते हैं?",
        "preferred_language": "hi"
    }, headers=tokens["customer"])
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["path"] in ("greeting", "chitchat")
    # Response should have Hindi greeting / acknowledgement
    assert len(data["reply"]) > 5


def test_langgraph_hindi_complaint_chat(tokens):
    r = client.post("/api/chat", json={
        "text": "मेरा इंटरनेट धीमा है स्पीड चेक करो",
        "preferred_language": "hi"
    }, headers=tokens["customer"])
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["path"] in ("diagnostic", "known_fix", "confirm_registration", "clarification", "incident_aware")


def test_voice_endpoint_validation(tokens):
    # Simulated voice upload with language parameter
    fake_audio = b"RIFF....WAVEfmt ...."
    r = client.post(
        "/api/chat/voice?language=hi",
        files={"file": ("test.webm", fake_audio, "audio/webm")},
        headers=tokens["customer"]
    )
    # Since Groq API is configured, if live it transcribes or if network error returns 503
    assert r.status_code in (200, 503)
