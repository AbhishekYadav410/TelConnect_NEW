"""End-to-end tests over the full PRD flow, run against a throwaway DB.

Order matters (module-scoped client): auth -> upload/ETL/ML -> analytics ->
incidents/root cause -> notifications -> assistant -> export.
"""
import os
import tempfile

os.environ["TCI_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["TCI_DISABLE_SCHEDULER"] = "1"

import pytest
from fastapi.testclient import TestClient

from app import db, ml, seed
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


# ---------- Layer 0: auth & role boundaries ----------
def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_login_bad_password():
    r = client.post("/api/auth/login", json={"email": "admin@telecom.com", "password": "wrong"})
    assert r.status_code == 401
    assert "incorrect password" in r.json()["detail"].lower()


def test_login_unregistered_user():
    r = client.post("/api/auth/login", json={"email": "unregistered_user@example.com", "password": "anypassword"})
    assert r.status_code == 401
    assert "not registered" in r.json()["detail"].lower()


def test_signup_and_login_customer():
    r = client.post("/api/auth/signup", json={
        "name": "Test User", "email": "test@example.com", "password": "pass1234",
        "region": "Dwarka, Delhi", "service_type": "voice"})
    assert r.status_code == 200 and r.json()["user"]["role"] == "customer"
    dup = client.post("/api/auth/signup", json={
        "name": "Test User", "email": "test@example.com", "password": "pass1234"})
    assert dup.status_code == 409


def test_signup_with_others_region():
    r = client.post("/api/auth/signup", json={
        "name": "Others Region User", "email": "others_user@example.com", "password": "pass1234",
        "region": "Others", "service_type": "broadband"})
    assert r.status_code == 200 and r.json()["user"]["region"] == "Others"


def test_customer_blocked_from_admin_routes(tokens):
    for path in ["/api/admin/analytics/summary", "/api/admin/incidents",
                 "/api/admin/queue", "/api/admin/heatmap", "/api/admin/alerts"]:
        assert client.get(path, headers=tokens["customer"]).status_code == 403


def test_admin_blocked_from_customer_chat(tokens):
    assert client.post("/api/chat", json={"text": "hi"}, headers=tokens["admin"]).status_code == 403


def test_unauthenticated_blocked():
    assert client.get("/api/admin/queue").status_code in (401, 403)
    assert client.post("/api/chat", json={"text": "hi"}).status_code in (401, 403)


# ---------- Layer 3: classifier quality gate ----------
def test_classifier_macro_f1_gate():
    metrics = ml.metrics()
    assert metrics["macro_f1"] >= 0.80, f"held-out macro-F1 {metrics['macro_f1']} below PRD gate"


def test_classifier_hinglish():
    cat, _ = ml.classify_category("net nahi chal raha hai subah se kaam ruk gaya")
    assert cat == "network"
    cat, _ = ml.classify_category("bill me extra charges laga diye maine use nahi kiya")
    assert cat == "billing"


# ---------- Layers 1-2: upload, mapping, ETL ----------
def test_upload_preview_and_ingest(tokens):
    csv_path = seed.ensure_seed_files()
    with open(csv_path, "rb") as f:
        preview = client.post("/api/admin/upload/preview",
                              files={"file": ("complaints.csv", f, "text/csv")},
                              headers=tokens["admin"]).json()
    mapping = preview["suggested_mapping"]
    assert mapping["text"] == "Complaint Description"
    assert mapping["region"] == "City Area"
    assert mapping["timestamp"] == "Created Date"
    # PII columns must never be auto-mapped
    assert "Customer Name" not in mapping.values()
    assert "Contact Number" not in mapping.values()

    import json as _json
    with open(csv_path, "rb") as f:
        r = client.post("/api/admin/upload/ingest",
                        files={"file": ("complaints.csv", f, "text/csv")},
                        data={"mapping": _json.dumps(mapping)}, headers=tokens["admin"])
    assert r.status_code == 200
    body = r.json()
    assert body["etl"]["inserted"] > 1000
    assert body["etl"]["deduplicated"] > 0          # duplicate channel rows collapsed
    assert body["scored"] == body["etl"]["inserted"]  # every row ML-scored


def test_pii_redacted_in_stored_text():
    row = db.connect().execute(
        "SELECT COUNT(*) c FROM complaints WHERE text LIKE '%+91-98%' "
        "OR text LIKE '%@gmail%'").fetchone()
    assert row["c"] == 0


def test_customer_cannot_upload(tokens):
    r = client.post("/api/admin/upload/preview",
                    files={"file": ("x.csv", b"a,b\n1,2", "text/csv")},
                    headers=tokens["customer"])
    assert r.status_code == 403


# ---------- Layer 5A: analytics ----------
def test_analytics_summary(tokens):
    s = client.get("/api/admin/analytics/summary", headers=tokens["admin"]).json()
    assert len(s["volume"]) > 5
    cats = {c["category"] for c in s["categories"]}
    assert {"network", "billing", "service"} <= cats
    assert s["resolution"]["total"] > 1000
    assert len(s["recurring_themes"]) > 0


def test_queue_has_summaries_and_factors(tokens):
    q = client.get("/api/admin/queue?limit=5", headers=tokens["admin"]).json()
    top = q["rows"][0]
    assert top["ticket_summary"]
    assert isinstance(top["priority_factors"], list) and len(top["priority_factors"]) >= 1



def test_filters_drilldown(tokens):
    q = client.get("/api/admin/queue?category=billing&limit=10", headers=tokens["admin"]).json()
    assert q["total"] > 0
    assert all(r["category"] == "billing" for r in q["rows"])


# ---------- Layer 7: heatmap + spike detection ----------
def test_heatmap_severity(tokens):
    cells = client.get("/api/admin/heatmap", headers=tokens["admin"]).json()
    by_region = {c["region"]: c for c in cells}
    assert "Raj Nagar, Ghaziabad" in by_region
    raj = by_region["Raj Nagar, Ghaziabad"]
    assert raj["severity"] == "high"          # injected spike shows red
    assert raj["lat"] and raj["long"]


def test_spike_detected_incident_opened(tokens):
    incs = client.get("/api/admin/incidents", headers=tokens["admin"]).json()
    raj = [i for i in incs if i["region"] == "Raj Nagar, Ghaziabad"]
    assert raj, "spike detector failed to open incident for injected spike"
    assert raj[0]["spike_pct"] > 100
    assert raj[0]["complaint_count"] >= 8


def test_admin_alert_inbox_fired(tokens):
    alerts = client.get("/api/admin/alerts", headers=tokens["admin"]).json()
    assert any("Raj Nagar" in a["draft_text"] for a in alerts)


def test_incident_ack(tokens):
    inc = client.get("/api/admin/incidents", headers=tokens["admin"]).json()[0]
    r = client.post(f"/api/admin/incidents/{inc['incident_id']}/ack",
                    json={"ack_status": "acknowledged"}, headers=tokens["admin"])
    assert r.json()["admin_ack_status"] == "acknowledged"


# ---------- Layer 6: root cause ----------
def test_root_cause_with_evidence_and_confidence(tokens):
    incs = client.get("/api/admin/incidents", headers=tokens["admin"]).json()
    raj = [i for i in incs if i["region"] == "Raj Nagar, Ghaziabad"][0]
    assert raj["root_cause"], "root cause not generated"
    assert raj["confidence"] and 0 < raj["confidence"] <= 100
    assert isinstance(raj["evidence"], list) and len(raj["evidence"]) >= 3  # PRD gate


# ---------- Layer 8: proactive notifications ----------
def test_notification_queue_and_approval(tokens):
    q = client.get("/api/admin/notifications/queue", headers=tokens["admin"]).json()
    pending = [n for n in q if n["approval_status"] == "pending"]
    assert pending, "no drafted customer notifications"
    # rohan (Raj Nagar + broadband) must be among the matched recipients
    rohan = [n for n in pending if n["customer_name"] == "Rohan Sharma"]
    assert rohan, "affected customer not matched to incident"
    n = rohan[0]
    assert n["match_reason"] and "region" in n["match_reason"]
    assert n["draft_text"]
    r = client.post(f"/api/admin/notifications/{n['notification_id']}/approval",
                    json={"status": "approved"}, headers=tokens["admin"])
    assert r.json()["status"] == "approved"


def test_customer_receives_approved_notification(tokens):
    # rohan is registered in Raj Nagar + broadband -> must be matched
    feed = client.get("/api/my/notifications", headers=tokens["customer"]).json()
    assert feed, "matched customer got no approved notification"
    assert feed[0]["incident_id"]


# ---------- Layer 5B: assistant ----------
def test_chat_incident_aware_no_duplicate_ticket(tokens):
    r = client.post("/api/chat", json={"text": "my broadband has been down since morning"},
                    headers=tokens["customer"]).json()
    assert r["meta"]["path"] == "incident_aware"
    assert "INC-" in r["reply"]
    # second ask must reuse the linked ticket, not create a duplicate
    r2 = client.post("/api/chat", json={"text": "internet still down, any update?"},
                     headers=tokens["customer"]).json()
    assert r2["meta"]["path"] in ("incident_aware", "status_lookup")
    tickets = client.get("/api/my/tickets", headers=tokens["customer"]).json()
    linked = [t for t in tickets if t["incident_id"]]
    assert len(linked) == 1, "duplicate ticket created for same incident"


def test_chat_known_fix_rag(tokens):
    # different customer, region without an open incident -> KB path
    cust2 = client.post("/api/auth/login",
                        json={"email": "priya@example.com", "password": "customer123"}).json()
    hdrs = {"Authorization": f"Bearer {cust2['token']}"}
    r = client.post("/api/chat", json={"text": "I recharged but money deducted and plan not active"},
                    headers=hdrs).json()
    assert r["meta"]["path"] == "known_fix"
    assert r["meta"]["source"]


def test_chat_register_verification_flow(tokens):
    """PRD 11.1: details summarised -> customer confirms -> ticket created."""
    cust2 = client.post("/api/auth/login",
                        json={"email": "priya@example.com", "password": "customer123"}).json()
    hdrs = {"Authorization": f"Bearer {cust2['token']}"}
    r = client.post("/api/chat", json={"text": "please register a complaint, my set top box remote "
                                               "is broken and I want a replacement"},
                    headers=hdrs).json()
    assert r["meta"]["path"] == "confirm_registration"     # verification step first
    assert "confirm" in r["reply"].lower() or "shall i" in r["reply"].lower()
    r2 = client.post("/api/chat", json={"text": "yes"}, headers=hdrs).json()
    assert r2["meta"]["path"] == "registered"
    ticket_id = r2["meta"]["complaint_id"]
    assert ticket_id in r2["reply"]
    row = db.connect().execute("SELECT * FROM complaints WHERE complaint_id=?",
                               (ticket_id,)).fetchone()
    assert row["status"] == "new"
    assert row["priority_label"] in ("P1", "P2", "P3", "P4")
    assert row["sla_deadline"]
    status = client.post("/api/chat", json={"text": "what is the status of my complaint?"},
                         headers=hdrs).json()
    assert status["meta"]["path"] == "status_lookup"
    assert status["meta"]["tickets"][0]["ticket_summary"]


def test_chat_hinglish(tokens):
    cust = client.post("/api/auth/login",
                       json={"email": "arjun@example.com", "password": "customer123"}).json()
    hdrs = {"Authorization": f"Bearer {cust['token']}"}
    r = client.post("/api/chat", json={"text": "net nahi chal raha subah se"}, headers=hdrs).json()
    assert r["meta"]["language"] in ("hinglish", "hi")
    assert r["meta"]["path"] in ("incident_aware", "known_fix", "registered", "confirm_registration")


# ---------- export + retrain ----------
def test_export_csv(tokens):
    r = client.get("/api/admin/export.csv?category=network", headers=tokens["admin"])
    assert r.status_code == 200
    lines = r.text.strip().splitlines()
    assert len(lines) > 100 and lines[0].startswith("complaint_id")


def test_retrain(tokens):
    m = client.post("/api/admin/ml/retrain", headers=tokens["admin"]).json()
    assert m["macro_f1"] >= 0.80


def test_chat_register_uses_prior_issue_context(tokens):
    """'register a complaint' after a failed fix must file the ORIGINAL issue, not the follow-up."""
    c = client.post("/api/auth/signup", json={
        "name": "Ctx User", "email": "ctx@example.com", "password": "ctx12345",
        "region": "Bandra, Mumbai", "service_type": "mobile data"}).json()
    hdrs = {"Authorization": f"Bearer {c['token']}"}
    client.post("/api/chat", json={"text": "mera 4G data bahut slow chal raha hai"}, headers=hdrs)
    r = client.post("/api/chat", json={"text": "that did not help, register a complaint"},
                    headers=hdrs).json()
    assert r["meta"]["path"] == "confirm_registration"
    r2 = client.post("/api/chat", json={"text": "yes please"}, headers=hdrs).json()
    assert r2["meta"]["path"] == "registered"
    row = db.connect().execute("SELECT text, category FROM complaints WHERE complaint_id=?",
                               (r2["meta"]["complaint_id"],)).fetchone()
    assert "slow" in row["text"]
    assert row["category"] == "network"


# ---------- PRD v6: lifecycle, confirmation loop, feedback, audit, SLA ----------
def _customer(email, region="Salt Lake, Kolkata", service="broadband"):
    r = client.post("/api/auth/login", json={"email": email, "password": "lifecycle1"})
    if r.status_code != 200:
        r = client.post("/api/auth/signup", json={
            "name": "Lifecycle User", "email": email, "password": "lifecycle1",
            "region": region, "service_type": service})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_resolution_confirmation_loop_closes_ticket(tokens):
    hdrs = _customer("loop1@example.com")
    client.post("/api/chat", json={"text": "register a complaint: landline instrument is broken"},
                headers=hdrs)
    r = client.post("/api/chat", json={"text": "yes"}, headers=hdrs).json()
    tid = r["meta"]["complaint_id"]
    # admin assigns + proposes a resolution
    a = client.patch(f"/api/admin/complaints/{tid}",
                     json={"assigned_to": "Field Ops"}, headers=tokens["admin"]).json()
    assert a["changed"]["assigned_to"] == "Field Ops"
    p = client.post(f"/api/admin/complaints/{tid}/propose-resolution",
                    json={"text": "Replacement instrument delivered and tested."},
                    headers=tokens["admin"]).json()
    assert p["status"] == "resolved_pending_confirmation"
    # customer confirms -> CLOSED, feedback requested
    c = client.post("/api/chat", json={"text": "yes it works now"}, headers=hdrs).json()
    assert c["meta"]["path"] == "resolution_confirmed"
    assert c["meta"]["expect"] == "rating"
    row = db.connect().execute("SELECT status, closed_at FROM complaints WHERE complaint_id=?",
                               (tid,)).fetchone()
    assert row["status"] == "closed" and row["closed_at"]
    # feedback rating captured
    f = client.post("/api/chat", json={"text": "5 great service"}, headers=hdrs).json()
    assert f["meta"]["path"] == "feedback_recorded" and f["meta"]["rating"] == 5
    fb = db.connect().execute("SELECT rating FROM feedback WHERE complaint_id=?", (tid,)).fetchone()
    assert fb["rating"] == 5
    # full immutable history exists
    hist = client.get(f"/api/admin/complaints/{tid}/history", headers=tokens["admin"]).json()
    transitions = [h["to_status"] for h in hist]
    assert transitions[0] == "new" and transitions[-1] == "closed"
    assert "resolved_pending_confirmation" in transitions


def test_resolution_rejection_reopens_and_escalates(tokens):
    hdrs = _customer("loop2@example.com")
    client.post("/api/chat", json={"text": "register a complaint: wifi speed drops every evening"},
                headers=hdrs)
    r = client.post("/api/chat", json={"text": "yes"}, headers=hdrs).json()
    tid = r["meta"]["complaint_id"]
    client.post(f"/api/admin/complaints/{tid}/propose-resolution",
                json={"text": "Channel width adjusted on your router."}, headers=tokens["admin"])
    rej = client.post("/api/chat", json={"text": "no, still broken"}, headers=hdrs).json()
    assert rej["meta"]["path"] == "resolution_rejected"
    row = db.connect().execute("SELECT status FROM complaints WHERE complaint_id=?", (tid,)).fetchone()
    assert row["status"] == "escalated"    # reopened then auto-escalated to support queue
    res = db.connect().execute("SELECT outcome FROM resolutions WHERE complaint_id=?", (tid,)).fetchone()
    assert res["outcome"] == "rejected"


def test_admin_status_update_visible_to_customer(tokens):
    hdrs = _customer("loop3@example.com")
    client.post("/api/chat", json={"text": "register a complaint: static noise on my landline"},
                headers=hdrs)
    r = client.post("/api/chat", json={"text": "haan"}, headers=hdrs).json()
    tid = r["meta"]["complaint_id"]
    client.patch(f"/api/admin/complaints/{tid}",
                 json={"status": "in_progress", "note": "Technician dispatched"},
                 headers=tokens["admin"])
    feed = client.get("/api/my/notifications", headers=hdrs).json()
    assert any(tid in n["draft_text"] and "in progress" in n["draft_text"] for n in feed)
    hist = client.get(f"/api/my/tickets/{tid}/history", headers=hdrs).json()
    assert hist[-1]["to_status"] == "in_progress"


def test_customer_cannot_read_others_history(tokens):
    hdrs_a = _customer("loop4@example.com")
    hdrs_b = _customer("loop5@example.com")
    client.post("/api/chat", json={"text": "register a complaint: no dial tone at all"}, headers=hdrs_a)
    r = client.post("/api/chat", json={"text": "yes"}, headers=hdrs_a).json()
    tid = r["meta"]["complaint_id"]
    assert client.get(f"/api/my/tickets/{tid}/history", headers=hdrs_b).status_code == 404


def test_audit_log_records_privileged_actions(tokens):
    audit = client.get("/api/admin/audit", headers=tokens["admin"]).json()
    actions = {a["action"] for a in audit}
    assert "ticket.update" in actions
    assert "ticket.propose_resolution" in actions
    assert "dataset.ingest" in actions
    assert client.get("/api/admin/audit").status_code in (401, 403)  # admin-only


def test_analytics_v6_fields(tokens):
    s = client.get("/api/admin/analytics/summary", headers=tokens["admin"]).json()
    res = s["resolution"]
    for key in ("closed", "escalated", "pending_confirmation", "sla_breaches",
                "priority_distribution", "avg_rating"):
        assert key in res
    assert any(p["priority_label"] == "P1" for p in res["priority_distribution"])


def test_voice_endpoint_requires_key_or_transcribes(tokens):
    hdrs = _customer("loop6@example.com")
    r = client.post("/api/chat/voice", files={"file": ("a.webm", b"\x1a\x45\xdf\xa3", "audio/webm")},
                    headers=hdrs)
    assert r.status_code in (200, 503)   # 503 offline (no GROQ key), 200 with key
    if r.status_code == 503:
        assert "GROQ_API_KEY" in r.json()["detail"]
    assert client.post("/api/chat/voice",
                       files={"file": ("a.webm", b"x", "audio/webm")}).status_code in (401, 403)


# ---------- Core Chatbot Feature Tests ----------
def test_chat_greeting_and_suggestions(tokens):
    hdrs = _customer("bot_greet@example.com")
    r = client.post("/api/chat", json={"text": "hello good morning"}, headers=hdrs).json()
    assert r["meta"]["path"] == "greeting"
    assert "suggestions" in r["meta"] and len(r["meta"]["suggestions"]) > 0

    thx = client.post("/api/chat", json={"text": "thank you so much"}, headers=hdrs).json()
    assert thx["meta"]["path"] == "chitchat"


def test_chat_smart_clarification(tokens):
    hdrs = _customer("bot_clarify@example.com")
    r = client.post("/api/chat", json={"text": "help me with my problem"}, headers=hdrs).json()
    assert r["meta"]["path"] == "clarification"
    assert "suggestions" in r["meta"] and len(r["meta"]["suggestions"]) > 0


def test_chat_billing_query_guidance(tokens):
    hdrs = _customer("bot_bill@example.com")
    r = client.post("/api/chat", json={"text": "how long does a duplicate charge refund take?"}, headers=hdrs).json()
    assert r["meta"]["path"] == "billing_query"
    assert "source" in r["meta"]


def test_chat_escalate_and_reopen_flow(tokens):
    hdrs = _customer("bot_esc@example.com")
    # First create a ticket
    client.post("/api/chat", json={"text": "register a complaint: optical fiber cable broken"}, headers=hdrs)
    r = client.post("/api/chat", json={"text": "yes"}, headers=hdrs).json()
    tid = r["meta"]["complaint_id"]

    # Escalate existing ticket
    esc = client.post("/api/chat", json={"text": "please connect me to a human agent"}, headers=hdrs).json()
    assert esc["meta"]["path"] == "escalated"
    assert esc["meta"]["complaint_id"] == tid

    # Admin marks closed
    client.patch(f"/api/admin/complaints/{tid}", json={"status": "closed", "note": "Resolved by tech"}, headers=tokens["admin"])

    # Customer reopens ticket
    reop = client.post("/api/chat", json={"text": "the issue came back, please reopen my complaint"}, headers=hdrs).json()
    assert reop["meta"]["path"] == "reopened"
    assert reop["meta"]["complaint_id"] == tid


# ---------- Admin AI Assistant End-to-End Tests ----------
def test_admin_ai_assistant_e2e(tokens):
    # Role boundaries
    assert client.post("/api/admin/assistant/chat", json={"text": "hello"}).status_code == 401
    assert client.post("/api/admin/assistant/chat", json={"text": "hello"}, headers=tokens["customer"]).status_code == 403

    # Immediate attention
    r1 = client.post("/api/admin/assistant/chat", json={"text": "Which complaints need immediate attention?"}, headers=tokens["admin"])
    assert r1.status_code == 200
    d1 = r1.json()
    assert "reply" in d1 and d1["meta"]["intent"] == "IMMEDIATE_ATTENTION"

    # Escalation risk
    r2 = client.post("/api/admin/assistant/chat", json={"text": "Which complaints have the highest escalation risk?"}, headers=tokens["admin"])
    assert r2.status_code == 200
    assert r2.json()["meta"]["intent"] == "ESCALATION_RISK"

    # Category breakdown
    r3 = client.post("/api/admin/assistant/chat", json={"text": "What are the top complaint categories?"}, headers=tokens["admin"])
    assert r3.status_code == 200
    assert r3.json()["meta"]["intent"] == "CATEGORY_BREAKDOWN"

    # Incident status & Root cause
    r4 = client.post("/api/admin/assistant/chat", json={"text": "What is the current incident status and likely root cause?"}, headers=tokens["admin"])
    assert r4.status_code == 200

    # Recommended action & RAG
    r5 = client.post("/api/admin/assistant/chat", json={"text": "What action should we take?"}, headers=tokens["admin"])
    assert r5.status_code == 200
    assert r5.json()["meta"]["intent"] == "RECOMMENDED_ACTION"

    # Summary
    r6 = client.post("/api/admin/assistant/chat", json={"text": "Summarize today's complaints."}, headers=tokens["admin"])
    assert r6.status_code == 200
    assert r6.json()["meta"]["intent"] == "SUMMARY"

    # History & Clear
    hist = client.get("/api/admin/assistant/history", headers=tokens["admin"]).json()
    assert len(hist) >= 6
    clr = client.post("/api/admin/assistant/clear", headers=tokens["admin"]).json()
    assert clr.get("cleared") is True
    assert len(client.get("/api/admin/assistant/history", headers=tokens["admin"]).json()) == 0


def test_customer_chat_clear(tokens):
    hdrs = tokens["customer"]
    # Send a message to populate history
    client.post("/api/chat", json={"text": "hello testing new chat"}, headers=hdrs)
    hist_before = client.get("/api/chat/history", headers=hdrs).json()
    assert len(hist_before) >= 2

    # Clear chat
    clr = client.post("/api/chat/clear", headers=hdrs).json()
    assert clr.get("ok") is True

    # Verify history is empty
    hist_after = client.get("/api/chat/history", headers=hdrs).json()
    assert len(hist_after) == 0



