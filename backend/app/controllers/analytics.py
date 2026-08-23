"""Layer 5A support — admin dashboard analytics queries.

Every endpoint is a straight SQL aggregate over the shared DB, filterable, with
drill-down and CSV export. All shaped for the React dashboard's charts.
"""
import csv
import io
import re
from collections import Counter

from .. import db


def _filters(params: dict) -> tuple[str, list]:
    clauses, args = [], []
    for field in ("category", "region", "service_type", "network_type", "status", "channel"):
        if params.get(field):
            clauses.append(f"{field} = ?")
            args.append(params[field])
    if params.get("search"):
        s = f"%{params['search'].strip()}%"
        clauses.append("(complaint_id LIKE ? OR text LIKE ? OR ticket_summary LIKE ? OR region LIKE ?)")
        args.extend([s, s, s, s])
    if params.get("since"):
        clauses.append("timestamp >= ?")
        args.append(params["since"])
    if params.get("until"):
        clauses.append("timestamp <= ?")
        args.append(params["until"])
    if params.get("min_severity"):
        clauses.append("priority_score >= ?")
        args.append(float(params["min_severity"]))
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", args


def volume_over_time(params: dict) -> list[dict]:
    where, args = _filters(params)
    rows = db.connect().execute(
        f"SELECT substr(timestamp,1,10) day, COUNT(*) count FROM complaints{where} "
        "GROUP BY day ORDER BY day", args).fetchall()
    return [dict(r) for r in rows]


def category_breakdown(params: dict) -> list[dict]:
    where, args = _filters(params)
    return [dict(r) for r in db.connect().execute(
        f"SELECT COALESCE(category,'unscored') category, COUNT(*) count "
        f"FROM complaints{where} GROUP BY category ORDER BY count DESC", args)]


def resolution_stats(params: dict) -> dict:
    where, args = _filters(params)
    now = db.now_iso()
    row = db.connect().execute(
        f"SELECT COUNT(*) total, SUM(status='closed') closed, "
        f"SUM(status IN ('new','reopened')) open, SUM(status='in_progress') in_progress, "
        f"SUM(status='escalated') escalated, "
        f"SUM(status='resolved_pending_confirmation') pending_confirmation, "
        f"SUM(status != 'closed' AND sla_deadline IS NOT NULL AND sla_deadline < ?) sla_breaches "
        f"FROM complaints{where}", [now] + args).fetchone()
    total = row["total"] or 0
    fb = db.connect().execute(
        "SELECT COUNT(*) c, ROUND(AVG(rating),2) avg_rating FROM feedback").fetchone()
    prio = db.connect().execute(
        f"SELECT priority_label, COUNT(*) count FROM complaints"
        f"{where + (' AND ' if where else ' WHERE ')}priority_label IS NOT NULL "
        f"AND status != 'closed' GROUP BY priority_label ORDER BY priority_label", args).fetchall()
    return {"total": total, "closed": row["closed"] or 0, "open": row["open"] or 0,
            "in_progress": row["in_progress"] or 0, "escalated": row["escalated"] or 0,
            "pending_confirmation": row["pending_confirmation"] or 0,
            "sla_breaches": row["sla_breaches"] or 0,
            "resolution_rate": round((row["closed"] or 0) / total, 3) if total else 0,
            "feedback_count": fb["c"], "avg_rating": fb["avg_rating"],
            "priority_distribution": [dict(p) for p in prio]}


def sentiment_trend(params: dict) -> list[dict]:
    where, args = _filters(params)
    prefix = "WHERE" if not where else where + " AND"
    return [dict(r) for r in db.connect().execute(
        f"SELECT substr(timestamp,1,10) day, ROUND(AVG(sentiment),3) avg_sentiment, "
        f"COUNT(*) count FROM complaints {prefix} sentiment IS NOT NULL "
        "GROUP BY day ORDER BY day", args)]


def risk_table(params: dict, limit: int = 20) -> list[dict]:
    where, args = _filters(params)
    prefix = "WHERE" if not where else where + " AND"
    return db.rows_to_dicts(db.connect().execute(
        f"SELECT complaint_id, ticket_summary, region, category, escalation_risk, "
        f"priority_score, priority_label, priority_factors, status, sla_deadline, assigned_to, "
        f"timestamp FROM complaints "
        f"{prefix} status != 'closed' AND escalation_risk IS NOT NULL "
        f"ORDER BY escalation_risk DESC LIMIT ?", args + [limit]).fetchall())


from ..services.geo import geocode_region


def region_density(params: dict) -> list[dict]:
    """Heatmap cells: per-region counts + rolling severity vs that region's own share."""
    where, args = _filters(params)
    rows = db.connect().execute(
        f"SELECT region, COUNT(*) count, AVG(lat) lat, AVG(long) long, "
        f"SUM(status != 'closed') open_count FROM complaints{where} "
        "GROUP BY region ORDER BY count DESC", args).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d["lat"] is None or d["long"] is None:
            geo = geocode_region(d["region"])
            if geo:
                d["lat"], d["long"] = geo
        out.append(d)
    if out:
        counts = sorted(d["count"] for d in out)
        median = counts[len(counts) // 2]
        p60 = counts[int(len(counts) * 0.6)]
        # "high" needs a real deviation (>=1.6x median), not just being top of a flat pack
        for d in out:
            d["severity"] = "high" if d["count"] >= max(p60 + 1, 1.6 * median) else (
                "medium" if d["count"] > p60 else "normal")
    return out


_STOP = set("the a an is in of for my to and it not no since has have been i on with at was "
            "very please help me this that kar ke ki ka se hai hain but".split())


def recurring_themes(params: dict, top: int = 10) -> list[dict]:
    """Top repeated complaint bigrams — surfaces recurring issue themes."""
    where, args = _filters(params)
    rows = db.connect().execute(f"SELECT text FROM complaints{where} LIMIT 5000", args).fetchall()
    grams: Counter = Counter()
    for r in rows:
        words = [w for w in re.findall(r"[a-z]+", r["text"].lower()) if w not in _STOP]
        grams.update(" ".join(p) for p in zip(words, words[1:]))
    return [{"theme": g, "count": c} for g, c in grams.most_common(top)]


def drilldown(params: dict, limit: int = 100, offset: int = 0) -> dict:
    where, args = _filters(params)
    conn = db.connect()
    total = conn.execute(f"SELECT COUNT(*) c FROM complaints{where}", args).fetchone()["c"]

    sort_by = params.get("sort_by", "newest")
    if sort_by == "priority":
        order_by = "priority_score DESC, timestamp DESC"
    elif sort_by == "risk":
        order_by = "escalation_risk DESC, priority_score DESC"
    elif sort_by == "oldest":
        order_by = "timestamp ASC, priority_score DESC"
    else:
        # Default: newest complaints first so live customer registrations appear immediately at the top
        order_by = "timestamp DESC, priority_score DESC"

    rows = db.rows_to_dicts(conn.execute(
        f"SELECT complaint_id, ticket_summary, text, category, region, service_type, channel, "
        f"sentiment_label, escalation_risk, priority_score, priority_label, priority_factors, "
        f"status, assigned_to, sla_deadline, incident_id, "
        f"timestamp FROM complaints{where} ORDER BY {order_by} "
        f"LIMIT ? OFFSET ?", args + [limit, offset]).fetchall())
    return {"total": total, "rows": rows}


def export_csv(params: dict) -> str:
    where, args = _filters(params)
    rows = db.connect().execute(
        f"SELECT complaint_id, timestamp, region, category, service_type, network_type, channel, "
        f"status, sentiment_label, escalation_risk, priority_score, ticket_summary, incident_id "
        f"FROM complaints{where} ORDER BY timestamp DESC", args).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([d[0] for d in db.connect().execute("SELECT complaint_id, timestamp, region, "
                     "category, service_type, network_type, channel, status, sentiment_label, "
                     "escalation_risk, priority_score, ticket_summary, incident_id FROM complaints "
                     "LIMIT 0").description])
    writer.writerows([tuple(r) for r in rows])
    return buf.getvalue()
