"""Layer 5B — Customer-Facing AI Assistant & Autonomous Agent.

Pipeline per PRD 5.2 + LangGraph multi-task workflow:
- Multilingual translation & normalization (DistilBERT + Groq)
- Multi-turn conversation state & intent router
- Proactive incident check + RAG knowledge retrieval
- Dynamic tools (speed diagnostics, ticket lifecycle, escalation, billing)
- Grounded conversational response synthesis (Groq LLM + offline fallback)
"""
import json
import re
from typing import Optional

from .. import db, ml
from ..agents.agent_graph import (
    DIAGNOSTIC_INTENT,
    ESCALATE_INTENT,
    GREETING_INTENT,
    ISSUE_RE,
    NO_RE,
    REGISTER_INTENT,
    REOPEN_INTENT,
    SPECIFIC_SYMPTOMS,
    STATUS_INTENT,
    THANKS_INTENT,
    YES_RE,
    _incident_note,
    _my_tickets,
    _open_incident_for,
    _pending_confirmation_ticket,
    register_complaint,
    run_agent_graph,
    run_network_diagnostic,
)
from ..services.etl import clean_text, detect_language, normalize_hinglish
from ..services import rag
from ..services.groq_client import groq_available, groq_chat_messages, groq_json_messages
from ..services.notify import notify_customer_event
from ..services.translator import to_english_semantics, translate_text

BILLING_QUERY = re.compile(
    r"(bill|charge|refund|plan|recharge|payment|invoice|autopay|deduct|tariff|balance).{0,40}\?|"
    r"(how|why|what|when|where|kaise|kyun|kab).{0,40}(bill|charge|refund|plan|recharge|payment|invoice|autopay|deduct)", re.I)


def is_vague_issue(text: str) -> bool:
    t = text.strip().lower()
    if len(t) < 40 and not SPECIFIC_SYMPTOMS.search(t):
        if re.search(r"\b(help|problem|issue|dikkat|pareshani|error|not working|facing|kuch|support|trouble|kharab|samasya)\b", t, re.I):
            return True
    return False


def _get_recent_messages(user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent chat history for conversation continuity."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT role, text, meta, created_at FROM chat_messages WHERE user_id=? "
        "ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    return list(reversed([dict(r) for r in rows]))


def _find_prior_issue_text(user_id: str, current_text: str = "") -> str:
    """Extract previous issue description from conversation history if user says 'register it'."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT text FROM chat_messages WHERE user_id=? AND role='user' "
        "ORDER BY created_at DESC LIMIT 8", (user_id,)).fetchall()
    for r in rows:
        t = r["text"].strip()
        if t != current_text.strip() and ISSUE_RE.search(t) and not REGISTER_INTENT.search(t):
            return t
    return current_text


def route_intent(text: str, state: dict, pending_ticket, user: dict | None = None) -> str:
    """PRD 5.1 & Core Features intent router — combines state, heuristics, and semantic rules."""
    # State continuations take first priority
    if state.get("mode") == "awaiting_registration_confirm":
        if YES_RE.search(text):
            return "CONFIRM_REGISTRATION"
        if NO_RE.search(text):
            return "CANCEL_REGISTRATION"
        return "RE_ROUTE"

    if state.get("mode") == "awaiting_feedback_rating":
        if re.search(r"[1-5]", text) or any(w in text.lower() for w in ("star", "good", "great", "poor", "bad")):
            return "GIVE_FEEDBACK"
        return "RE_ROUTE"

    if pending_ticket is not None and YES_RE.search(text):
        return "CONFIRM_RESOLUTION"
    if pending_ticket is not None and NO_RE.search(text):
        return "REJECT_RESOLUTION"

    if state.get("mode") == "awaiting_fix_feedback":
        if YES_RE.search(text):
            return "FIX_WORKED"
        if NO_RE.search(text):
            return "FIX_FAILED"

    # Dynamic line diagnostics
    if DIAGNOSTIC_INTENT.search(text):
        return "DIAGNOSTIC"

    # Explicit user actions
    if ESCALATE_INTENT.search(text):
        return "ESCALATE"
    if REOPEN_INTENT.search(text):
        return "REOPEN_COMPLAINT"
    if STATUS_INTENT.search(text) and not REGISTER_INTENT.search(text):
        return "CHECK_STATUS"
    if GREETING_INTENT.search(text) and not ISSUE_RE.search(text) and not REGISTER_INTENT.search(text):
        return "GREETING"
    if THANKS_INTENT.search(text) and not ISSUE_RE.search(text):
        return "THANKS"
    if BILLING_QUERY.search(text) and not REGISTER_INTENT.search(text):
        return "BILLING_QUERY"
    if is_vague_issue(text) and not REGISTER_INTENT.search(text):
        return "CLARIFY"
    if REGISTER_INTENT.search(text) or ISSUE_RE.search(text):
        return "REPORT_COMPLAINT"
    return "GENERAL_QUERY"


def _registration_preview(user: dict, text: str, language: str = "en") -> tuple[str, dict]:
    """PRD 11.1 — summarise extracted details and ask for confirmation before creating."""
    category, _conf = ml.classify_category(text)
    clean_desc = clean_text(text)[:160]
    region = user.get('region') or 'Not specified'
    service = user.get('service_type') or 'General'

    if language == "hi":
        preview = (f"शिकायत दर्ज करने से पहले कृपया विवरण की पुष्टि करें:\n"
                   f"• समस्या: {clean_desc}\n"
                   f"• श्रेणी: {category.capitalize()}\n"
                   f"• क्षेत्र: {region}\n"
                   f"• सेवा: {service}\n\n"
                   f"क्या मैं आपका टिकट बना दूँ? (yes / no)")
    else:
        preview = (f"Let me confirm before I register this complaint:\n"
                   f"• Issue: {clean_desc}\n"
                   f"• Category: {category.capitalize()}\n"
                   f"• Region: {region}\n"
                   f"• Service: {service}\n\n"
                   f"Shall I create the ticket? (yes / no)")
    return preview, {"mode": "awaiting_registration_confirm", "text": text, "category": category}


def handle_message(user: dict, text: str, preferred_language: Optional[str] = None) -> dict:
    """Core message processing delegating to LangGraph workflow."""
    return run_agent_graph(user, text, preferred_language=preferred_language)


def chat(user: dict, text: str, preferred_language: Optional[str] = None) -> dict:
    """Entry point for customer chat messages."""
    conn = db.connect()
    conn.execute("INSERT INTO chat_messages(message_id,user_id,role,text,created_at) VALUES(?,?,?,?,?)",
                 (db.new_id("MSG"), user["user_id"], "user", text, db.now_iso()))

    result = handle_message(user, text, preferred_language=preferred_language)

    conn.execute(
        "INSERT INTO chat_messages(message_id,user_id,role,text,meta,created_at) VALUES(?,?,?,?,?,?)",
        (db.new_id("MSG"), user["user_id"], "assistant", result["reply"],
         json.dumps({k: v for k, v in result["meta"].items() if k in
                     ("language", "intent", "path", "source", "complaint_id", "incident_id",
                      "expect", "rating", "suggestions", "diagnostic")}), db.now_iso()))
    conn.commit()
    return result


def history(user_id: str, limit: int = 50) -> list[dict]:
    return db.rows_to_dicts(db.connect().execute(
        "SELECT * FROM chat_messages WHERE user_id=? ORDER BY created_at LIMIT ?",
        (user_id, limit)).fetchall())


def clear_history(user_id: str) -> None:
    """Clear conversation history for a customer."""
    conn = db.connect()
    conn.execute("DELETE FROM chat_messages WHERE user_id=?", (user_id,))
    conn.commit()

