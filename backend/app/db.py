"""Layer 4 — shared SQLite database. Single source of truth.

ponytail: SQLite instead of PostgreSQL — same schema/SQL at demo scale, zero setup.
Swap DB_PATH + connect() for psycopg when hardening.
"""
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

def get_db_path() -> str:
    return os.environ.get(
        "TCI_DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tci.db"),
    )


DB_PATH = get_db_path()
_local = threading.local()


def connect() -> sqlite3.Connection:
    """One connection per thread (FastAPI + scheduler threads)."""
    path = get_db_path()
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
        _local.path = path
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    role          TEXT NOT NULL CHECK (role IN ('admin','customer')),
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    region        TEXT,
    service_type  TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id    TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES users(user_id),
    text            TEXT NOT NULL,
    raw_text        TEXT,
    category        TEXT,
    category_confidence REAL,
    channel         TEXT,
    timestamp       TEXT NOT NULL,
    region          TEXT,
    lat             REAL,
    long            REAL,
    service_type    TEXT,
    network_type    TEXT,
    device          TEXT,
    sentiment       REAL,
    sentiment_label TEXT,
    sentiment_confidence REAL,
    urgency         INTEGER DEFAULT 0,
    escalation_risk REAL,
    escalation_reason TEXT,
    priority_score  REAL,
    priority_factors TEXT,
    priority_reason TEXT,
    ticket_summary  TEXT,
    language        TEXT,
    status          TEXT DEFAULT 'new' CHECK (status IN
        ('new','in_progress','waiting_for_customer','escalated',
         'resolved_pending_confirmation','reopened','closed')),
    resolution      TEXT,
    priority_label  TEXT,
    sla_deadline    TEXT,
    assigned_to     TEXT,
    resolved_at     TEXT,
    closed_at       TEXT,
    incident_id     TEXT,
    source          TEXT DEFAULT 'upload',
    dedupe_key      TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_complaints_region ON complaints(region);
CREATE INDEX IF NOT EXISTS idx_complaints_ts ON complaints(timestamp);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id     TEXT PRIMARY KEY,
    region          TEXT NOT NULL,
    service_type    TEXT,
    opened_at       TEXT NOT NULL,
    complaint_count INTEGER,
    spike_pct       REAL,
    root_cause      TEXT,
    confidence      REAL,
    evidence        TEXT,
    status          TEXT DEFAULT 'open' CHECK (status IN ('open','investigating','resolved')),
    admin_ack_status TEXT DEFAULT 'unacknowledged'
        CHECK (admin_ack_status IN ('unacknowledged','acknowledged','assigned'))
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    incident_id     TEXT REFERENCES incidents(incident_id),
    recipient_type  TEXT NOT NULL CHECK (recipient_type IN ('admin','customer')),
    recipient_id    TEXT,
    draft_text      TEXT NOT NULL,
    match_reason    TEXT,
    approval_status TEXT DEFAULT 'pending' CHECK (approval_status IN ('pending','approved','rejected')),
    read            INTEGER DEFAULT 0,
    sent_at         TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id  TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(user_id),
    role        TEXT NOT NULL CHECK (role IN ('user','assistant')),
    text        TEXT NOT NULL,
    meta        TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kb_docs (
    doc_id     TEXT PRIMARY KEY,
    kind       TEXT NOT NULL CHECK (kind IN ('sop','resolved_ticket','incident_writeup')),
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    category   TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS complaint_status_history (
    history_id   TEXT PRIMARY KEY,
    complaint_id TEXT NOT NULL REFERENCES complaints(complaint_id),
    from_status  TEXT,
    to_status    TEXT NOT NULL,
    actor        TEXT NOT NULL,
    reason       TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_complaint ON complaint_status_history(complaint_id);

CREATE TABLE IF NOT EXISTS resolutions (
    resolution_id TEXT PRIMARY KEY,
    complaint_id  TEXT NOT NULL REFERENCES complaints(complaint_id),
    proposed_by   TEXT NOT NULL,
    source        TEXT NOT NULL CHECK (source IN ('rag','incident','admin','ai')),
    text          TEXT NOT NULL,
    outcome       TEXT DEFAULT 'pending' CHECK (outcome IN ('pending','confirmed','rejected')),
    created_at    TEXT NOT NULL,
    decided_at    TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id  TEXT PRIMARY KEY,
    complaint_id TEXT NOT NULL REFERENCES complaints(complaint_id),
    customer_id  TEXT REFERENCES users(user_id),
    rating       INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    user_id    TEXT PRIMARY KEY REFERENCES users(user_id),
    state      TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id   TEXT PRIMARY KEY,
    actor_id   TEXT,
    actor_role TEXT,
    action     TEXT NOT NULL,
    target     TEXT,
    detail     TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db() -> None:
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    # Safe backward-compatible column migration for existing databases
    try:
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(complaints)").fetchall()}
        new_cols = [
            ("category_confidence", "REAL"),
            ("sentiment_confidence", "REAL"),
            ("priority_reason", "TEXT"),
            ("escalation_reason", "TEXT"),
        ]
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}")
        conn.commit()
    except Exception:
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def rows_to_dicts(rows) -> list:
    out = []
    for r in rows:
        d = dict(r)
        for k in ("evidence", "priority_factors", "meta"):
            if k in d and isinstance(d[k], str) and d[k].startswith(("[", "{")):
                try:
                    d[k] = json.loads(d[k])
                except ValueError:
                    pass
        out.append(d)
    return out


def get_meta(key: str, default=None):
    row = connect().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(key: str, value: str) -> None:
    connect().execute(
        "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    connect().commit()


OPEN_STATUSES = ("new", "in_progress", "waiting_for_customer", "escalated",
                 "resolved_pending_confirmation", "reopened")


def record_status(complaint_id: str, from_status, to_status: str, actor: str,
                  reason: str = "") -> None:
    """Immutable status-transition record (PRD v6 4.1)."""
    connect().execute(
        "INSERT INTO complaint_status_history(history_id,complaint_id,from_status,to_status,"
        "actor,reason,created_at) VALUES(?,?,?,?,?,?,?)",
        (new_id("HIS"), complaint_id, from_status, to_status, actor, reason, now_iso()))


def set_status(complaint_id: str, to_status: str, actor: str, reason: str = "") -> str | None:
    """Transition a complaint's status + write history. Returns previous status."""
    conn = connect()
    row = conn.execute("SELECT status FROM complaints WHERE complaint_id=?",
                       (complaint_id,)).fetchone()
    if row is None:
        return None
    stamps = ""
    if to_status == "resolved_pending_confirmation":
        stamps = ", resolved_at='" + now_iso() + "'"
    elif to_status == "closed":
        stamps = ", closed_at='" + now_iso() + "'"
    conn.execute(f"UPDATE complaints SET status=?{stamps} WHERE complaint_id=?",
                 (to_status, complaint_id))
    record_status(complaint_id, row["status"], to_status, actor, reason)
    conn.commit()
    return row["status"]


def audit(actor_id, actor_role: str, action: str, target: str = "", detail: str = "") -> None:
    """Audit trail for privileged operations (PRD v6 3.1 / 7 module 16)."""
    connect().execute(
        "INSERT INTO audit_logs(audit_id,actor_id,actor_role,action,target,detail,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (new_id("AUD"), actor_id, actor_role, action, target, detail[:500], now_iso()))
    connect().commit()


def get_conv_state(user_id: str) -> dict:
    row = connect().execute("SELECT state FROM conversations WHERE user_id=?",
                            (user_id,)).fetchone()
    if row and row["state"]:
        import json as _json
        try:
            return _json.loads(row["state"])
        except ValueError:
            return {}
    return {}


def set_conv_state(user_id: str, state: dict) -> None:
    import json as _json
    connect().execute(
        "INSERT INTO conversations(user_id,state,updated_at) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, updated_at=excluded.updated_at",
        (user_id, _json.dumps(state), now_iso()))
    connect().commit()
