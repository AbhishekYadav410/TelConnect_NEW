"""Tests for Telecom Domain Restriction in both Admin and Customer Chatbots."""
import os
import tempfile

os.environ["TCI_DISABLE_SCHEDULER"] = "1"

import pytest
from fastapi.testclient import TestClient

from app import db, seed
from app.services.telecom_filter import TELECOM_RESTRICTION_MESSAGE, is_telecom_related
from backend.app.routes.main import app, startup_tasks

startup_tasks()
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    old_db = os.environ.get("TCI_DB_PATH")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_restriction.db")
    os.environ["TCI_DB_PATH"] = db_path
    db.init_db()
    seed.seed_accounts()
    seed.seed_kb()
    yield
    if old_db is not None:
        os.environ["TCI_DB_PATH"] = old_db
    else:
        os.environ.pop("TCI_DB_PATH", None)
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def tokens():
    admin = client.post("/api/auth/login",
                        json={"email": "admin@telecom.com", "password": "admin123"}).json()
    cust = client.post("/api/auth/login",
                       json={"email": "rohan@example.com", "password": "customer123"}).json()
    return {
        "admin": {"Authorization": f"Bearer {admin['token']}"},
        "customer": {"Authorization": f"Bearer {cust['token']}"}
    }


def test_domain_filter_unit_allow_and_reject():
    """Unit tests for telecom domain filter classifier."""
    allow_samples = [
        "What is 5G?",
        "What is 4G?",
        "What is VoLTE?",
        "What is VoWiFi?",
        "What is an eSIM?",
        "What is a SIM card?",
        "Why is my SIM not working?",
        "Why is my mobile internet slow?",
        "Why is my network signal weak?",
        "How can I activate roaming?",
        "What is international roaming?",
        "How can I check my data balance?",
        "What are the available recharge plans?",
        "Why can't I make calls?",
        "Why can't I send SMS?",
        "What is APN?",
        "Why is my phone showing EDGE instead of 4G?",
        "What is the difference between 4G and 5G?",
        "What is network coverage?",
        "What is edge computing in telecom?",
        "What is my mobile network?",
        "मेरा इंटरनेट धीमा है",
        "नेट नहीं चल रहा है",
        "रिचार्ज कैसे करें",
        "सिम काम नहीं कर रहा",
    ]

    reject_samples = [
        "What is the meaning of edge?",
        "Who is the president of India?",
        "What is the capital of France?",
        "Tell me a joke.",
        "Write Python code.",
        "Solve this mathematics problem.",
        "What is photosynthesis?",
        "Tell me about World War 2.",
        "Write a poem.",
        "What is the meaning of a random English word?",
        "What is a network?",
        "What is a neural network?",
        "What is a social network?",
        "भारत का राष्ट्रपति कौन है?",
        "एक चुटकुला सुनाओ",
        "कविता लिखो",
    ]

    for q in allow_samples:
        assert is_telecom_related(q, is_admin=False) is True, f"Failed to ALLOW valid telecom query: {q}"

    for q in reject_samples:
        assert is_telecom_related(q, is_admin=False) is False, f"Failed to REJECT non-telecom query: {q}"


def test_customer_chatbot_rejects_unrelated_queries(tokens):
    """Customer Chatbot must reject non-telecom questions with predefined restriction message."""
    unrelated_queries = [
        "What is the meaning of edge?",
        "Who is the president of India?",
        "What is the capital of France?",
        "Tell me a joke.",
        "Write Python code.",
        "Solve this mathematics problem.",
        "What is photosynthesis?",
        "Tell me about World War 2.",
        "Write a poem.",
        "What is the meaning of a random English word?",
        "What is a network?",
    ]

    for query in unrelated_queries:
        r = client.post("/api/chat", json={"text": query, "preferred_language": "en"}, headers=tokens["customer"])
        assert r.status_code == 200
        data = r.json()
        assert data["reply"] == TELECOM_RESTRICTION_MESSAGE, f"Expected domain restriction for: {query}"
        assert data["meta"]["intent"] == "RESTRICTED_NON_TELECOM"


def test_customer_chatbot_allows_valid_telecom_queries(tokens):
    """Customer Chatbot must answer valid telecom questions."""
    telecom_queries = [
        "What is 5G?",
        "What is 4G?",
        "What is VoLTE?",
        "What is VoWiFi?",
        "What is an eSIM?",
        "What is a SIM card?",
        "Why is my SIM not working?",
        "Why is my mobile internet slow?",
        "Why is my network signal weak?",
        "How can I activate roaming?",
        "What is international roaming?",
        "How can I check my data balance?",
        "What are the available recharge plans?",
        "Why can't I make calls?",
        "Why can't I send SMS?",
        "What is APN?",
        "Why is my phone showing EDGE instead of 4G?",
        "What is the difference between 4G and 5G?",
        "What is network coverage?",
        "What is edge computing in telecom?",
        "What is my mobile network?",
    ]

    for query in telecom_queries:
        r = client.post("/api/chat", json={"text": query, "preferred_language": "en"}, headers=tokens["customer"])
        assert r.status_code == 200
        data = r.json()
        assert data["reply"] != TELECOM_RESTRICTION_MESSAGE, f"Valid telecom query was rejected: {query}"
        assert len(data["reply"]) > 10


def test_admin_chatbot_rejects_unrelated_queries(tokens):
    """Admin Chatbot must reject non-telecom questions with predefined restriction message."""
    unrelated_queries = [
        "What is the meaning of edge?",
        "Who is the president of India?",
        "What is the capital of France?",
        "Tell me a joke.",
        "Write Python code.",
        "Solve this mathematics problem.",
        "What is photosynthesis?",
        "Tell me about World War 2.",
        "Write a poem.",
        "What is a network?",
    ]

    for query in unrelated_queries:
        r = client.post("/api/admin/assistant/chat", json={"text": query}, headers=tokens["admin"])
        assert r.status_code == 200
        data = r.json()
        assert data["reply"] == TELECOM_RESTRICTION_MESSAGE, f"Admin chatbot failed to reject: {query}"
        assert data["meta"]["intent"] == "RESTRICTED_NON_TELECOM"


def test_admin_chatbot_allows_valid_operations_and_telecom_queries(tokens):
    """Admin Chatbot must answer valid operational and telecom inquiries."""
    admin_queries = [
        "give most recurring complaint",
        "number of internet complaints category",
        "how many billing complaints",
        "Which complaints need immediate attention?",
        "Which complaints have the highest escalation risk?",
        "What are the top complaint categories?",
        "Why are complaints increasing in Raj Nagar, Ghaziabad?",
        "What is the current incident status?",
        "What is the likely root cause?",
        "What action should we take for router red light and broadband issues?",
        "Summarize today's complaints.",
        "What is 5G network slicing?",
        "What is edge computing in telecom?",
    ]

    for query in admin_queries:
        r = client.post("/api/admin/assistant/chat", json={"text": query}, headers=tokens["admin"])
        assert r.status_code == 200
        data = r.json()
        assert data["reply"] != TELECOM_RESTRICTION_MESSAGE, f"Valid admin query was rejected: {query}"
        assert len(data["reply"]) > 10
