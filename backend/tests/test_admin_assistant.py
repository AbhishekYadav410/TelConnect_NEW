"""Comprehensive tests for the Admin AI Assistant endpoint and capabilities."""
import os
import tempfile

from backend.app.controllers import admin_assistant
from backend.app.services import rag

os.environ["TCI_DISABLE_SCHEDULER"] = "1"

import pytest
from fastapi.testclient import TestClient

from app import db, ml, seed
from backend.app.routes.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    old_db = os.environ.get("TCI_DB_PATH")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_admin.db")
    os.environ["TCI_DB_PATH"] = db_path
    db.init_db()
    seed.seed_accounts()
    seed.seed_kb()
    conn = db.connect()
    ts = db.now_iso()
    user_row = conn.execute("SELECT user_id FROM users WHERE email='rohan@example.com'").fetchone()
    cust_id = user_row["user_id"] if user_row else "USR-admin"
    conn.execute(
        "INSERT INTO complaints(complaint_id,customer_id,text,raw_text,channel,timestamp,region,"
        "service_type,category,sentiment,sentiment_label,urgency,escalation_risk,priority_score,"
        "priority_label,sla_deadline,priority_factors,ticket_summary,language,status,source,created_at) "
        "VALUES('CMP-TEST-001',?,'Broadband fiber cut','Broadband fiber cut','chat',?,'Raj Nagar, Ghaziabad',"
        "'broadband','network',-0.8,'Negative',1,0.85,0.92,'P1',?,'[\"Optical fiber cut\"]','Broadband down in Raj Nagar','en','new','test',?)",
        (cust_id, ts, ts, ts)
    )
    conn.execute(
        "INSERT INTO complaints(complaint_id,customer_id,text,raw_text,channel,timestamp,region,"
        "service_type,category,sentiment,sentiment_label,urgency,escalation_risk,priority_score,"
        "priority_label,sla_deadline,priority_factors,ticket_summary,language,status,source,created_at) "
        "VALUES('CMP-TEST-002',?,'Double billing deduction','Double billing deduction','chat',?,'Connaught Place, Delhi',"
        "'broadband','billing',-0.6,'Negative',1,0.75,0.80,'P2',?,'[\"Double billing\"]','Double billing deduction','en','new','test',?)",
        (cust_id, ts, ts, ts)
    )
    conn.commit()
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



def test_admin_assistant_unauthorized():
    """Unauthenticated users must be rejected."""
    r = client.post("/api/admin/assistant/chat", json={"text": "Hello"})
    assert r.status_code == 401


def test_admin_assistant_customer_forbidden(tokens):
    """Customer role must not access admin AI assistant."""
    r = client.post("/api/admin/assistant/chat", json={"text": "Hello"}, headers=tokens["customer"])
    assert r.status_code == 403


def test_admin_assistant_empty_query(tokens):
    """Empty query must be rejected."""
    r = client.post("/api/admin/assistant/chat", json={"text": "   "}, headers=tokens["admin"])
    assert r.status_code == 400


def test_admin_assistant_immediate_attention(tokens):
    """Admin asks which complaints need immediate attention."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "Which complaints need immediate attention?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert "meta" in data
    assert len(data["reply"]) > 20
    assert data["meta"]["intent"] == "IMMEDIATE_ATTENTION"


def test_admin_assistant_escalation_risk(tokens):
    """Admin asks about complaints with highest escalation risk."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "Which complaints have the highest escalation risk?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] == "ESCALATION_RISK"
    assert "Escalation Risk" in data["reply"] or "risk" in data["reply"].lower()


def test_admin_assistant_top_categories(tokens):
    """Admin asks about top complaint categories."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "What are the top complaint categories?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] == "CATEGORY_BREAKDOWN"
    # Should mention major categories
    assert any(cat in data["reply"].lower() for cat in ("network", "billing", "service", "device"))


def test_admin_assistant_increasing_complaints(tokens):
    """Admin asks why complaints are increasing in a region."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "Why are complaints increasing in Raj Nagar, Ghaziabad?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert len(data["reply"]) > 10


def test_admin_assistant_incident_status(tokens):
    """Admin asks about current incident status."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "What is the current incident status?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] in ("INCIDENT_STATUS", "REGION_SPIKE", "GENERAL_OPS")


def test_admin_assistant_root_cause(tokens):
    """Admin asks what is the likely root cause."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "What is the likely root cause?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] in ("ROOT_CAUSE", "INCIDENT_STATUS", "REGION_SPIKE")


def test_admin_assistant_recommended_action_and_rag(tokens):
    """Admin asks what action should be taken (tests ChromaDB RAG SOP retrieval)."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "What action should we take for router red light and broadband issues?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] == "RECOMMENDED_ACTION"
    # Should include action steps
    assert len(data["reply"]) > 20


def test_admin_assistant_summary(tokens):
    """Admin asks to summarize complaints."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "Summarize today's complaints."
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] == "SUMMARY"
def test_admin_assistant_category_reasoning(tokens):
    """Admin asks why a complaint was classified into a category."""
    r = client.post("/api/admin/assistant/chat", json={
        "text": "Why was this complaint classified as Network?"
    }, headers=tokens["admin"])
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert data["meta"]["intent"] == "CATEGORY_REASONING"
    assert "Primary Category: Network" in data["reply"]
    assert "Evidence:" in data["reply"]
    assert "Related Categories:" in data["reply"]


def test_admin_assistant_history_and_clear(tokens):
    """Admin can view history and clear conversation."""
    hist = client.get("/api/admin/assistant/history", headers=tokens["admin"]).json()
    assert isinstance(hist, list)
    assert len(hist) >= 2

    # Clear history
    clr = client.post("/api/admin/assistant/clear", headers=tokens["admin"]).json()
    assert clr.get("cleared") is True

    hist_after = client.get("/api/admin/assistant/history", headers=tokens["admin"]).json()
    assert len(hist_after) == 0
