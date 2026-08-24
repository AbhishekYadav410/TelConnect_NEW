"""FastAPI app — all routes, role-gated, plus the background pipeline scheduler.

Run:  uvicorn app.main:app --port 8000        (from backend/; no --reload — it would
                                               start the scheduler thread twice)
"""
import csv
import io
import json
import os
import threading
import time

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..agents import agent_graph
from ..controllers import admin_assistant, auth
from .. import analytics, assistant, db, ml, notify, seed, translator
from ..services import etl, incidents, rag
from ..services.groq_client import groq_available

def startup_tasks() -> None:
    """Idempotent init: schema, demo accounts, KB, seed CSV, ML models, RAG index, scheduler."""
    global _scheduler_started
    db.init_db()
    seed.seed_accounts()
    seed.seed_kb()
    seed.ensure_seed_files()
    # Load pre-trained offline ML models (no training at startup)
    ml.predict_category("system init")
    rag.rebuild_index()
    if not _scheduler_started and os.environ.get("TCI_DISABLE_SCHEDULER") != "1":
        threading.Thread(target=_scheduler_loop, daemon=True).start()
        _scheduler_started = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    startup_tasks()
    yield


# Allowed CORS origins: support environment variable CORS_ORIGINS or default to localhost + vercel.app
cors_env = os.environ.get("CORS_ORIGINS", "")
allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
if not allowed_origins:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
    ]

app = FastAPI(title="Telecom Complaint Intelligence Platform", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if not any("*" in o for o in allowed_origins) else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEDULER_INTERVAL = int(os.environ.get("TCI_SCHEDULER_INTERVAL", "60"))
_scheduler_started = False


def pipeline_cycle() -> dict:
    """ETL/ML/incident/notification tick. Gated: only runs once an admin has ingested data."""
    if db.get_meta("ingest_done") != "1":
        return {"skipped": "no dataset ingested yet"}
    scored = ml.score_unscored()
    inc = incidents.run_cycle()
    drafted = notify.run_cycle()
    if scored:
        rag.rebuild_index()
    return {"scored": scored, **inc, "notifications_drafted": drafted}


def _scheduler_loop():
    while True:
        time.sleep(SCHEDULER_INTERVAL)
        try:
            pipeline_cycle()
        except Exception as exc:  # keep the loop alive; surface in logs
            print(f"[scheduler] cycle failed: {exc}")


# ---------- auth ----------
class SignupBody(BaseModel):
    name: str
    email: str
    password: str
    region: str | None = None
    service_type: str | None = None


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup")
def signup(body: SignupBody):
    """Customer self-signup. Admin accounts are provisioned, not self-served."""
    user = auth.create_user("customer", body.name, body.email, body.password,
                            body.region, body.service_type)
    return auth.login(body.email, body.password) | {"user": user}


@app.post("/api/auth/login")
def login(body: LoginBody):
    return auth.login(body.email, body.password)


@app.get("/api/auth/me")
def me(user: dict = Depends(auth.current_user)):
    user.pop("password_hash", None)
    return user


# ---------- admin: dataset upload + schema mapping ----------
@app.post("/api/admin/upload/preview")
async def upload_preview(file: UploadFile = File(...), _admin: dict = Depends(auth.require_admin)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig", errors="replace")))
    sample = []
    for i, row in enumerate(reader):
        if i >= 3:
            break
        sample.append(row)
    headers = reader.fieldnames or []
    if not headers:
        raise HTTPException(status_code=400, detail="Could not read CSV headers")
    return {"headers": headers, "sample": sample,
            "suggested_mapping": etl.suggest_mapping(headers, sample)}


@app.post("/api/admin/upload/ingest")
async def upload_ingest(file: UploadFile = File(...), mapping: str = Form(...),
                        _admin: dict = Depends(auth.require_admin)):
    content = await file.read()
    try:
        mapping_dict = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="mapping must be JSON")
    if not mapping_dict.get("text"):
        raise HTTPException(status_code=400, detail="mapping.text (complaint text column) is required")
    result = etl.ingest_csv(content, mapping_dict)
    db.audit(_admin["user_id"], "admin", "dataset.ingest", file.filename or "csv",
             json.dumps(result))
    db.set_meta("ingest_done", "1")
    scored = ml.score_unscored()
    rag.rebuild_index()
    cycle = pipeline_cycle()
    return {"etl": result, "scored": scored, "pipeline": cycle}


@app.post("/api/admin/pipeline/run")
def run_pipeline(_admin: dict = Depends(auth.require_admin)):
    """Manual 'refresh now' — same tick the scheduler runs."""
    return pipeline_cycle()


# ---------- admin: analytics ----------
def _params(category: str | None = None, region: str | None = None,
            service_type: str | None = None, network_type: str | None = None,
            status: str | None = None, channel: str | None = None,
            since: str | None = None, until: str | None = None,
            min_severity: str | None = None, search: str | None = None,
            sort_by: str | None = None) -> dict:
    return {k: v for k, v in locals().items() if v}


@app.get("/api/admin/analytics/summary")
def analytics_summary(params: dict = Depends(_params), _admin: dict = Depends(auth.require_admin)):
    return {
        "volume": analytics.volume_over_time(params),
        "categories": analytics.category_breakdown(params),
        "resolution": analytics.resolution_stats(params),
        "sentiment_trend": analytics.sentiment_trend(params),
        "recurring_themes": analytics.recurring_themes(params),
        "groq_live": groq_available(),
    }


@app.get("/api/admin/analytics/risk")
def analytics_risk(params: dict = Depends(_params), _admin: dict = Depends(auth.require_admin)):
    return analytics.risk_table(params)


@app.get("/api/admin/queue")
def queue(limit: int = 50, offset: int = 0, params: dict = Depends(_params),
          _admin: dict = Depends(auth.require_admin)):
    return analytics.drilldown(params, limit=limit, offset=offset)


@app.get("/api/admin/heatmap")
def heatmap(params: dict = Depends(_params), _admin: dict = Depends(auth.require_admin)):
    return analytics.region_density(params)


@app.get("/api/admin/export.csv")
def export(params: dict = Depends(_params), _admin: dict = Depends(auth.require_admin)):
    return PlainTextResponse(analytics.export_csv(params), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=complaints.csv"})


# ---------- admin: incidents / root cause ----------
@app.get("/api/admin/incidents")
def list_incidents(_admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT * FROM incidents ORDER BY opened_at DESC").fetchall())


@app.post("/api/admin/incidents/{incident_id}/investigate")
def investigate(incident_id: str, _admin: dict = Depends(auth.require_admin)):
    result = incidents.investigate(incident_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Incident not found or evidence too thin")
    return result


class AckBody(BaseModel):
    ack_status: str  # acknowledged / assigned


@app.post("/api/admin/incidents/{incident_id}/ack")
def ack_incident(incident_id: str, body: AckBody, _admin: dict = Depends(auth.require_admin)):
    if body.ack_status not in ("acknowledged", "assigned"):
        raise HTTPException(status_code=400, detail="ack_status must be acknowledged|assigned")
    conn = db.connect()
    cur = conn.execute("UPDATE incidents SET admin_ack_status=? WHERE incident_id=?",
                       (body.ack_status, incident_id))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.audit(_admin["user_id"], "admin", "incident.ack", incident_id, body.ack_status)
    return {"incident_id": incident_id, "admin_ack_status": body.ack_status}


@app.post("/api/admin/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str, _admin: dict = Depends(auth.require_admin)):
    conn = db.connect()
    cur = conn.execute("UPDATE incidents SET status='resolved' WHERE incident_id=?", (incident_id,))
    linked = conn.execute("SELECT complaint_id, status FROM complaints WHERE incident_id=? "
                          "AND status != 'closed'", (incident_id,)).fetchall()
    for c in linked:
        db.record_status(c["complaint_id"], c["status"], "closed",
                         f"admin:{_admin['user_id']}", f"incident {incident_id} resolved")
    conn.execute("UPDATE complaints SET status='closed', closed_at=?, "
                 "resolution='Incident resolved' WHERE incident_id=? AND status != 'closed'",
                 (db.now_iso(), incident_id))
    conn.commit()
    db.audit(_admin["user_id"], "admin", "incident.resolve", incident_id,
             f"{len(linked)} linked complaints closed")
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"incident_id": incident_id, "status": "resolved"}


# ---------- admin: alert inbox + notification approval queue ----------
@app.get("/api/admin/alerts")
def admin_alerts(_admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT n.*, i.region, i.status AS incident_status, i.admin_ack_status FROM notifications n "
        "LEFT JOIN incidents i ON i.incident_id=n.incident_id "
        "WHERE n.recipient_type='admin' ORDER BY n.created_at DESC LIMIT 50").fetchall())


@app.post("/api/admin/alerts/{notification_id}/read")
def mark_alert_read(notification_id: str, _admin: dict = Depends(auth.require_admin)):
    conn = db.connect()
    conn.execute("UPDATE notifications SET read=1 WHERE notification_id=?", (notification_id,))
    conn.commit()
    return {"ok": True}


@app.get("/api/admin/notifications/queue")
def notification_queue(_admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT n.*, u.name AS customer_name, i.region AS incident_region "
        "FROM notifications n LEFT JOIN users u ON u.user_id=n.recipient_id "
        "LEFT JOIN incidents i ON i.incident_id=n.incident_id "
        "WHERE n.recipient_type='customer' AND n.incident_id IS NOT NULL "
        "AND (n.match_reason LIKE '%region%' OR n.match_reason LIKE '%service%') "
        "ORDER BY n.approval_status='pending' DESC, "
        "n.created_at DESC LIMIT 200").fetchall())


class ApprovalBody(BaseModel):
    status: str  # approved / rejected


@app.post("/api/admin/notifications/{notification_id}/approval")
def set_notification_approval(notification_id: str, body: ApprovalBody,
                              _admin: dict = Depends(auth.require_admin)):
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved|rejected")
    result = notify.set_approval(notification_id, body.status)
    if result["updated"] == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.audit(_admin["user_id"], "admin", "notification.approval", notification_id, body.status)
    return result


@app.post("/api/admin/incidents/{incident_id}/draft-notifications")
def draft_notifications(incident_id: str, _admin: dict = Depends(auth.require_admin)):
    return notify.draft_for_incident(incident_id)


# ---------- admin: ML ----------
@app.get("/api/admin/ml/metrics")
def ml_metrics(_admin: dict = Depends(auth.require_admin)):
    return ml.metrics()


@app.post("/api/admin/ml/retrain")
def ml_retrain(_admin: dict = Depends(auth.require_admin)):
    return ml.train()


# ---------- admin: ticket management (PRD v6 modules 3-6, 16) ----------
VALID_STATUSES = ("new", "in_progress", "waiting_for_customer", "escalated",
                  "resolved_pending_confirmation", "reopened", "closed")
TEAMS = ("Field Ops", "RF Team", "Billing Team", "Support L2", "Network Ops")


class TicketUpdateBody(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
    note: str | None = None


@app.patch("/api/admin/complaints/{complaint_id}")
def update_ticket(complaint_id: str, body: TicketUpdateBody,
                  _admin: dict = Depends(auth.require_admin)):
    conn = db.connect()
    row = conn.execute("SELECT * FROM complaints WHERE complaint_id=?", (complaint_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    changed = {}
    if body.assigned_to is not None:
        conn.execute("UPDATE complaints SET assigned_to=? WHERE complaint_id=?",
                     (body.assigned_to or None, complaint_id))
        conn.commit()
        changed["assigned_to"] = body.assigned_to
        db.record_status(complaint_id, row["status"], row["status"],
                         f"admin:{_admin['user_id']}", f"assigned to {body.assigned_to}")
        if row["customer_id"]:
            notify.notify_customer_event(
                row["customer_id"],
                f"Ticket {complaint_id} is now with {body.assigned_to}.", "ticket assigned")
    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")
        db.set_status(complaint_id, body.status, f"admin:{_admin['user_id']}",
                      body.note or "admin status update")
        changed["status"] = body.status
        if row["customer_id"]:
            notify.notify_customer_event(
                row["customer_id"],
                f"Ticket {complaint_id} status updated to {body.status.replace('_', ' ')}."
                + (f" Note: {body.note}" if body.note else ""), "status changed")
    if not changed:
        raise HTTPException(status_code=400, detail="Nothing to update")
    db.audit(_admin["user_id"], "admin", "ticket.update", complaint_id, json.dumps(changed))
    return {"complaint_id": complaint_id, "changed": changed}


class ResolutionBody(BaseModel):
    text: str


@app.post("/api/admin/complaints/{complaint_id}/propose-resolution")
def propose_resolution(complaint_id: str, body: ResolutionBody,
                       _admin: dict = Depends(auth.require_admin)):
    """PRD 11.3 — admin proposes a fix; ticket waits for CUSTOMER confirmation to close."""
    conn = db.connect()
    row = conn.execute("SELECT * FROM complaints WHERE complaint_id=?", (complaint_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    conn.execute(
        "INSERT INTO resolutions(resolution_id,complaint_id,proposed_by,source,text,created_at) "
        "VALUES(?,?,?,?,?,?)",
        (db.new_id("RES"), complaint_id, f"admin:{_admin['user_id']}", "admin",
         body.text, db.now_iso()))
    conn.execute("UPDATE complaints SET resolution=? WHERE complaint_id=?",
                 (body.text, complaint_id))
    conn.commit()
    db.set_status(complaint_id, "resolved_pending_confirmation",
                  f"admin:{_admin['user_id']}", "resolution proposed")
    if row["customer_id"]:
        notify.notify_customer_event(
            row["customer_id"],
            f"A fix has been applied to ticket {complaint_id}: {body.text} "
            f"Please confirm in the assistant whether your service is working.",
            "resolution proposed")
    db.audit(_admin["user_id"], "admin", "ticket.propose_resolution", complaint_id, body.text[:200])
    return {"complaint_id": complaint_id, "status": "resolved_pending_confirmation"}


@app.get("/api/admin/complaints/{complaint_id}/history")
def ticket_history(complaint_id: str, _admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT * FROM complaint_status_history WHERE complaint_id=? ORDER BY created_at",
        (complaint_id,)).fetchall())


@app.get("/api/admin/audit")
def audit_log(limit: int = 100, _admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall())


@app.get("/api/admin/feedback")
def feedback_list(_admin: dict = Depends(auth.require_admin)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT f.*, u.name customer_name FROM feedback f LEFT JOIN users u "
        "ON u.user_id=f.customer_id ORDER BY f.created_at DESC LIMIT 100").fetchall())


@app.get("/api/admin/teams")
def teams(_admin: dict = Depends(auth.require_admin)):
    return list(TEAMS)


# ---------- admin: AI assistant ----------
class AdminChatBody(BaseModel):
    text: str


@app.post("/api/admin/assistant/chat")
def admin_chat(body: AdminChatBody, _admin: dict = Depends(auth.require_admin)):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    return admin_assistant.chat(_admin, body.text.strip())


@app.get("/api/admin/assistant/history")
def admin_chat_history(_admin: dict = Depends(auth.require_admin)):
    return admin_assistant.history(_admin["user_id"])


@app.post("/api/admin/assistant/clear")
def admin_chat_clear(_admin: dict = Depends(auth.require_admin)):
    return admin_assistant.clear_history(_admin["user_id"])


# ---------- translation & multilingual services ----------
class TranslateBody(BaseModel):
    text: str
    target_lang: str
    source_lang: str | None = None


@app.post("/api/translate")
def translate_endpoint(body: TranslateBody):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text to translate")
    return translator.translate_text(body.text.strip(), target_lang=body.target_lang, source_lang=body.source_lang)


# ---------- customer: assistant (the ONLY customer surface) ----------
class ChatBody(BaseModel):
    text: str
    preferred_language: str | None = None


@app.post("/api/chat")
def chat(body: ChatBody, user: dict = Depends(auth.require_customer)):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    return assistant.chat(user, body.text.strip(), preferred_language=body.preferred_language)


@app.get("/api/chat/history")
def chat_history(user: dict = Depends(auth.require_customer)):
    return assistant.history(user["user_id"])


@app.post("/api/chat/clear")
def clear_customer_chat_history(user: dict = Depends(auth.require_customer)):
    assistant.clear_history(user["user_id"])
    return {"ok": True, "message": "Conversation history cleared"}



@app.post("/api/chat/diagnostic")
def chat_diagnostic(user: dict = Depends(auth.require_customer)):
    """Run dynamic line speed and connectivity diagnostics for the customer."""
    diag = agent_graph.run_network_diagnostic(user)
    return diag


@app.get("/api/my/tickets")
def my_tickets(user: dict = Depends(auth.require_customer)):
    return db.rows_to_dicts(db.connect().execute(
        "SELECT complaint_id, ticket_summary, status, category, incident_id, timestamp "
        "FROM complaints WHERE customer_id=? ORDER BY timestamp DESC", (user["user_id"],)).fetchall())


@app.get("/api/my/notifications")
def my_notifications(user: dict = Depends(auth.require_customer)):
    return notify.customer_feed(user["user_id"])


@app.get("/api/my/tickets/{complaint_id}/history")
def my_ticket_history(complaint_id: str, user: dict = Depends(auth.require_customer)):
    """Status transparency (PRD 11.2) — a customer sees only their OWN ticket's history."""
    row = db.connect().execute(
        "SELECT customer_id FROM complaints WHERE complaint_id=?", (complaint_id,)).fetchone()
    if row is None or row["customer_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="Ticket not found on your account")
    return db.rows_to_dicts(db.connect().execute(
        "SELECT to_status, actor, reason, created_at FROM complaint_status_history "
        "WHERE complaint_id=? ORDER BY created_at", (complaint_id,)).fetchall())


@app.post("/api/chat/voice")
async def chat_voice(file: UploadFile = File(...), language: str | None = None,
                     user: dict = Depends(auth.require_customer)):
    """Multilingual voice transcription via Groq Whisper with Hindi/Hinglish/English support."""
    from ..services.groq_client import transcribe_audio
    audio = await file.read()
    if len(audio) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio too large (10MB max)")
    text = transcribe_audio(audio, file.filename or "audio.webm", language=language)
    if text is None:
        raise HTTPException(status_code=503,
                            detail="Voice transcription needs a GROQ_API_KEY (offline fallback "
                                   "covers text chat only). Please type your message.")
    detected = translator.detect_language(text)
    return {"text": text, "detected_language": detected}


# ---------- misc ----------
@app.get("/")
@app.get("/healthz")
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "TelConnect Backend",
        "groq_live": groq_available(),
        "ingest_done": db.get_meta("ingest_done") == "1",
    }



@app.get("/api/demo/sample-csv")
def sample_csv():
    """Serves the generated demo dataset so the upload flow can be demoed instantly."""
    path = seed.ensure_seed_files()
    with open(path) as f:
        return PlainTextResponse(f.read(), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=sample_complaints.csv"})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.routes.main:app", host="0.0.0.0", port=port, reload=False)

