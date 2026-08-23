"""Layer 8 — proactive customer notification engine.

For each incident: match registered customers whose region + active service overlap,
draft a plain-language message via Groq (fixed safe template fallback — never invents
an ETA or unconfirmed cause), queue for admin approval (human-in-the-loop, PRD NFR).
On approval the notification is linked to the customer's account; the assistant and
the customer's notification feed both surface it.
"""
from .. import db
from .groq_client import groq_chat


def notify_customer_event(user_id: str, text: str, reason: str,
                          incident_id: str | None = None) -> None:
    """Transactional in-app notification for a ticket event — auto-delivered per
    PRD v6 13.1 (only MASS incident notifications need admin approval)."""
    conn = db.connect()
    conn.execute(
        "INSERT INTO notifications(notification_id,incident_id,recipient_type,recipient_id,"
        "draft_text,match_reason,approval_status,sent_at,created_at) "
        "VALUES(?,?, 'customer', ?, ?, ?, 'approved', ?, ?)",
        (db.new_id("NTF"), incident_id, user_id, text, reason, db.now_iso(), db.now_iso()))
    conn.commit()


def match_affected_customers(incident: dict) -> list[dict]:
    rows = db.connect().execute(
        "SELECT user_id, name, region, service_type FROM users "
        "WHERE role='customer' AND region=? AND (service_type=? OR ? IS NULL)",
        (incident["region"], incident["service_type"], incident["service_type"])).fetchall()
    return [dict(r) for r in rows]


def draft_for_incident(incident_id: str) -> dict:
    """Create pending notifications for all matched customers (skips ones already drafted)."""
    conn = db.connect()
    row = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
    if row is None:
        return {"drafted": 0, "matched": 0}
    incident = dict(row)
    matched = match_affected_customers(incident)
    template = (f"We're aware of a {incident['service_type'] or 'network'} issue affecting your area "
                f"({incident['region']}). Our network team is investigating it"
                + (f" — likely cause: {incident['root_cause'].lower()}" if incident["root_cause"] else "")
                + f". Your account has been linked to incident {incident_id}; you don't need to "
                  f"contact support. We'll update you as soon as it's resolved.")
    draft = groq_chat(
        system="Draft a short, calm, plain-language customer notification for a telecom incident. "
               "Rules: reference the incident ID, do NOT invent an ETA, do NOT state any cause "
               "beyond the confirmed one provided, max 60 words, no marketing tone.",
        user=f"Incident {incident_id}: {incident['service_type']} issue in {incident['region']}. "
             f"Confirmed likely cause: {incident['root_cause'] or 'under investigation'}. "
             f"Status: {incident['status']}.",
        fallback=template, max_tokens=250)
    if not draft or not draft.strip():
        draft = template
    drafted = 0
    match_reason = (f"region = {incident['region']}; service = {incident['service_type']}; "
                    f"status = active connection")
    for cust in matched:
        exists = conn.execute(
            "SELECT 1 FROM notifications WHERE incident_id=? AND recipient_id=?",
            (incident_id, cust["user_id"])).fetchone()
        if exists:
            continue
        conn.execute(
            "INSERT INTO notifications(notification_id,incident_id,recipient_type,recipient_id,"
            "draft_text,match_reason,approval_status,created_at) "
            "VALUES(?,?, 'customer', ?, ?, ?, 'pending', ?)",
            (db.new_id("NTF"), incident_id, cust["user_id"], draft, match_reason, db.now_iso()))
        drafted += 1
    conn.commit()
    return {"drafted": drafted, "matched": len(matched), "draft_text": draft}


def run_cycle() -> int:
    """Draft notifications for every incident that has a root cause but no customer drafts yet."""
    total = 0
    for row in db.connect().execute(
            "SELECT incident_id FROM incidents WHERE status != 'resolved' AND root_cause IS NOT NULL"):
        total += draft_for_incident(row["incident_id"])["drafted"]
    return total


def set_approval(notification_id: str, status: str) -> dict:
    conn = db.connect()
    sent_at = db.now_iso() if status == "approved" else None
    cur = conn.execute(
        "UPDATE notifications SET approval_status=?, sent_at=? "
        "WHERE notification_id=? AND recipient_type='customer'",
        (status, sent_at, notification_id))
    conn.commit()
    return {"updated": cur.rowcount, "status": status}


def customer_feed(user_id: str) -> list[dict]:
    """Approved notifications for this customer (their proactive-notify inbox)."""
    return db.rows_to_dicts(db.connect().execute(
        "SELECT n.*, i.region, i.service_type, i.status AS incident_status FROM notifications n "
        "LEFT JOIN incidents i ON i.incident_id = n.incident_id "
        "WHERE n.recipient_id=? AND n.approval_status='approved' ORDER BY n.created_at DESC",
        (user_id,)).fetchall())
