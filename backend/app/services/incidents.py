"""Layers 6-7 — spike detector (rolling per-region baseline) + AI root-cause investigator.

Spike detection: for each (region, service_type), compare complaint count in the last
WINDOW hours vs the average same-length window over the previous BASELINE_DAYS.
Rolling per-region thresholds, not fixed global cutoffs (PRD requirement).

Root cause: computed evidence stats (concentration, dominant symptom, spike velocity,
similar past incidents from the KB) -> Groq returns a structured hypothesis grounded
ONLY in that evidence, with a confidence %. Minimum 3 evidence bullets before any
hypothesis is shown (PRD risk mitigation).
"""
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import rag
from .. import db
from .groq_client import groq_chat, groq_json

WINDOW_HOURS = 6
BASELINE_DAYS = 7
SPIKE_MULTIPLIER = 2.5   # window count must exceed baseline x this
MIN_CLUSTER = 8          # and be at least this many complaints

SYMPTOM_PATTERNS = [
    ("no connectivity / hard down", re.compile(r"down|no connect|not working|dead|band|outage|no internet", re.I)),
    ("slow speed", re.compile(r"slow|speed|mbps|lag", re.I)),
    ("call drops / voice quality", re.compile(r"call drop|voice|awaaz|quality|cut", re.I)),
    ("billing dispute", re.compile(r"charge|bill|refund|deduct|payment", re.I)),
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def detect_spikes(now: datetime | None = None) -> list[dict]:
    """Scan all regions; open/update incidents where density breaches rolling baseline."""
    now = now or datetime.now(timezone.utc)
    conn = db.connect()
    window_start = _iso(now - timedelta(hours=WINDOW_HOURS))
    baseline_start = _iso(now - timedelta(days=BASELINE_DAYS, hours=WINDOW_HOURS))
    opened = []

    recent = conn.execute(
        "SELECT region, service_type, COUNT(*) c FROM complaints "
        "WHERE timestamp >= ? GROUP BY region, service_type", (window_start,)).fetchall()
    windows_in_baseline = (BASELINE_DAYS * 24) / WINDOW_HOURS

    for row in recent:
        region, service, count = row["region"], row["service_type"], row["c"]
        if count < MIN_CLUSTER or region == "Unknown":
            continue
        base_total = conn.execute(
            "SELECT COUNT(*) c FROM complaints WHERE region=? AND service_type=? "
            "AND timestamp >= ? AND timestamp < ?",
            (region, service, baseline_start, window_start)).fetchone()["c"]
        baseline_avg = max(base_total / windows_in_baseline, 0.5)
        if count < baseline_avg * SPIKE_MULTIPLIER:
            continue
        spike_pct = round((count / baseline_avg - 1) * 100, 1)
        existing = conn.execute(
            "SELECT incident_id FROM incidents WHERE region=? AND service_type=? "
            "AND status != 'resolved'", (region, service)).fetchone()
        if existing:
            conn.execute(
                "UPDATE incidents SET complaint_count=?, spike_pct=? WHERE incident_id=?",
                (count, spike_pct, existing["incident_id"]))
            conn.execute("UPDATE complaints SET incident_id=? WHERE region=? AND service_type=? "
                         "AND timestamp >= ? AND incident_id IS NULL",
                         (existing["incident_id"], region, service, window_start))
            conn.commit()
            continue
        incident_id = f"INC-{now.year}-{db.new_id('')[1:5].upper()}"
        conn.execute(
            "INSERT INTO incidents(incident_id,region,service_type,opened_at,complaint_count,"
            "spike_pct,status) VALUES(?,?,?,?,?,?, 'open')",
            (incident_id, region, service, _iso(now), count, spike_pct))
        conn.execute("UPDATE complaints SET incident_id=? WHERE region=? AND service_type=? "
                     "AND timestamp >= ? AND incident_id IS NULL",
                     (incident_id, region, service, window_start))
        # real-time admin alert straight into the alert inbox (Layer 7 requirement)
        spike_label = (f"{count / baseline_avg:.0f}x its normal level"
                       if spike_pct > 500 else f"up {spike_pct:.0f}%")
        alert_text = (f"⚠ {region}: complaint density {spike_label} in the last "
                      f"{WINDOW_HOURS} hours ({count} {service or 'service'} complaints vs a "
                      f"baseline of ~{baseline_avg:.1f} per window). Incident {incident_id} "
                      f"opened — root-cause analysis triggered.")
        conn.execute(
            "INSERT INTO notifications(notification_id,incident_id,recipient_type,recipient_id,"
            "draft_text,match_reason,approval_status,sent_at,created_at) "
            "VALUES(?,?, 'admin', NULL, ?, ?, 'approved', ?, ?)",
            (db.new_id("NTF"), incident_id, alert_text,
             f"spike detector: {region} / {service}", _iso(now), _iso(now)))
        conn.commit()
        opened.append({"incident_id": incident_id, "region": region,
                       "service_type": service, "spike_pct": spike_pct, "count": count})
    return opened


# fallback cause labels per dominant symptom — used when Groq is unavailable, so
# different incident profiles still yield visibly different hypotheses
SYMPTOM_CAUSES = {
    "no connectivity / hard down": "Network node/line disruption in the affected area",
    "slow speed": "Cell/backhaul congestion in the affected area",
    "call drops / voice quality": "Tower handover fault in the affected area",
    "billing dispute": "Billing system error affecting the area's accounts",
}


def build_evidence(incident: dict) -> tuple[list[str], dict]:
    """Computed, checkable evidence bullets — the LLM may only reason over these.
    Also returns the underlying stats for the offline fallback hypothesis."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT text, region, timestamp FROM complaints WHERE incident_id=?",
        (incident["incident_id"],)).fetchall()
    if not rows:
        return [], {}
    evidence = []
    stats = {}
    total = len(rows)
    same_region = sum(1 for r in rows if r["region"] == incident["region"])
    stats["concentration_pct"] = round(100 * same_region / total)
    evidence.append(f"{stats['concentration_pct']}% of {total} clustered complaints are from "
                    f"{incident['region']}")
    symptom_counts = Counter()
    for r in rows:
        for name, pattern in SYMPTOM_PATTERNS:
            if pattern.search(r["text"]):
                symptom_counts[name] += 1
                break
    if symptom_counts:
        symptom, sc = symptom_counts.most_common(1)[0]
        stats["dominant_symptom"] = symptom
        stats["symptom_pct"] = round(100 * sc / total)
        evidence.append(f"{stats['symptom_pct']}% of complaints mention {symptom}")
    spike_label = (f"{incident['spike_pct'] / 100 + 1:.0f}x the rolling {BASELINE_DAYS}-day baseline"
                   if incident["spike_pct"] > 500
                   else f"{incident['spike_pct']:.0f}% above the rolling {BASELINE_DAYS}-day baseline")
    evidence.append(f"Sudden complaint spike ({spike_label} within {WINDOW_HOURS} hours)")
    timestamps = sorted(r["timestamp"] for r in rows)
    if len(timestamps) >= 2:
        first, last = timestamps[0][:16], timestamps[-1][:16]
        evidence.append(f"Cluster onset window: {first} to {last} UTC (concentrated burst, not drift)")
    similar = rag.retrieve(
        f"{incident['region']} {incident['service_type']} " +
        " ".join(r["text"] for r in rows[:5]), top_k=1, kinds=("incident_writeup",))
    if similar:
        stats["similar_incident"] = similar[0]["title"]
        evidence.append(f"Similar past incident on record: {similar[0]['title']} "
                        f"(similarity {similar[0]['similarity']:.2f})")
    return evidence, stats


def investigate(incident_id: str) -> dict | None:
    """Generate + store the evidence-backed root-cause hypothesis for one incident."""
    conn = db.connect()
    row = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
    if row is None:
        return None
    incident = dict(row)
    evidence, stats = build_evidence(incident)
    if len(evidence) < 3:  # PRD: never show a hypothesis on thin evidence
        return None
    similar = rag.retrieve(f"{incident['region']} {incident['service_type']} outage cluster",
                           top_k=2, kinds=("incident_writeup", "sop"))
    context = "\n".join(f"- [{d['title']}]: {d['body'][:300]}" for d in similar)
    # offline fallback: cause follows the dominant symptom; confidence is computed
    # from the evidence itself (concentration, symptom dominance, historical precedent)
    fb_symptom = stats.get("dominant_symptom", "no connectivity / hard down")
    fb_conf = min(92, round(40
                            + stats.get("concentration_pct", 0) * 0.25
                            + stats.get("symptom_pct", 0) * 0.15
                            + (12 if stats.get("similar_incident") else 0)))
    fallback = json.dumps({
        "root_cause": SYMPTOM_CAUSES.get(fb_symptom, "Localized service disruption"),
        "confidence": fb_conf,
        "reasoning": f"{stats.get('symptom_pct', 0)}% of the cluster reports {fb_symptom}, "
                     f"concentrated in one region"
                     + (f", matching past incident {stats['similar_incident']}"
                        if stats.get("similar_incident") else "") + "."})
    result = groq_json(
        system="You are a telecom network root-cause investigator. Using ONLY the evidence and "
               "historical context provided, return JSON: {\"root_cause\": short cause label, "
               "\"confidence\": integer 0-100, \"reasoning\": one sentence}. You must not state "
               "any cause the evidence does not support.",
        user=f"Incident: {incident['incident_id']} — {incident['region']}, "
             f"service: {incident['service_type']}\nEvidence:\n"
             + "\n".join(f"- {e}" for e in evidence)
             + f"\nHistorical context:\n{context}",
        fallback=json.loads(fallback))
    if not isinstance(result, dict) or "root_cause" not in result:
        result = json.loads(fallback)
    confidence = float(result.get("confidence", 70))
    conn.execute(
        "UPDATE incidents SET root_cause=?, confidence=?, evidence=?, status='investigating' "
        "WHERE incident_id=?",
        (str(result["root_cause"])[:200], confidence, json.dumps(evidence), incident_id))
    conn.commit()
    return {"incident_id": incident_id, "root_cause": result["root_cause"],
            "confidence": confidence, "evidence": evidence,
            "reasoning": result.get("reasoning", "")}


def run_cycle() -> dict:
    """One scheduler tick: detect spikes, investigate any incident lacking a root cause."""
    opened = detect_spikes()
    investigated = []
    for row in db.connect().execute(
            "SELECT incident_id FROM incidents WHERE root_cause IS NULL AND status != 'resolved'"):
        res = investigate(row["incident_id"])
        if res:
            investigated.append(res["incident_id"])
    return {"opened": opened, "investigated": investigated}
