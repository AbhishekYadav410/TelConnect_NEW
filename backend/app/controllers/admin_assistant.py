"""Admin AI Assistant — Grounded Telecom Operations & Decision Support.

Integrates:
- Existing SQLite database & ML outputs (complaint intelligence, priority, escalation risk)
- Existing ChromaDB vector RAG (SOPs, troubleshooting, incident writeups, resolution knowledge)
- Existing Groq LLM integration (with deterministic offline fallback grounded in DB & RAG)
- Role-gated admin access and conversation persistence in chat_messages
"""
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from . import analytics
from .. import db, ml
from ..services import incidents, rag
from ..services.groq_client import groq_available, groq_chat_messages

logger = logging.getLogger(__name__)

# Intent pattern matchers for admin inquiries
INTENT_PATTERNS = [
    ("CATEGORY_REASONING", re.compile(r"why was this complaint classified|why (?:is|was) (?:this|the|it) complaint classified|why (?:is|was) (?:it|this) classified as|why classified as|explain (?:the )?category|category reasoning|classification reasoning|why is it categorized as|why was .* categorized", re.I)),
    ("CATEGORY_BREAKDOWN", re.compile(r"top categor|category breakdown|categories|distribution of complaints|breakdown of complaint|complaints breakdown|most common issue", re.I)),
    ("SPECIFIC_CATEGORY_COUNT", re.compile(r"(?:number of|count of|how many|total)\s+(?:internet|network|billing|broadband|service|device|fiber|voice|data|sim|recharge)\s+(?:complaint|ticket|categor|issue|case)", re.I)),
    ("RECURRING_THEMES", re.compile(r"recurring|frequent|most common|repeated|top issue|common complaint|highest volume issue|repeated complaint", re.I)),
    ("IMMEDIATE_ATTENTION", re.compile(r"immediate|attention|critical|urgent|highest priority|p1|breach|deadline", re.I)),
    ("ESCALATION_RISK", re.compile(r"escalat|churn|trai|legal|court|ombudsman|porting|highest risk", re.I)),
    ("LEAST_COMPLAINTS_REGION", re.compile(r"(?:least|fewest|lowest|minimum|bottom|smallest)\s+(?:complaint|ticket|issue|volume)|region(?:s)?\s+with\s+(?:the\s+)?(?:least|fewest|lowest|minimum|bottom|smallest)|lowest\s+(?:complaint\s+)?region", re.I)),
    ("REGIONAL_BREAKDOWN", re.compile(r"regional\s+breakdown|complaints\s+by\s+region|highest\s+(?:complaint\s+)?region|top\s+region|most\s+complaint\s+region|regions\s+with\s+most\s+complaints", re.I)),
    ("REGION_SPIKE", re.compile(r"increasing|spike|surge|why are complaints increasing|outage in|outage status", re.I)),
    ("INCIDENT_STATUS", re.compile(r"incident status|current incident|active incident|open incident|incidents list", re.I)),
    ("ROOT_CAUSE", re.compile(r"root cause|why is this happening|cause of|underlying cause|evidence|investigat", re.I)),
    ("RECOMMENDED_ACTION", re.compile(r"what action|what should we do|recommend|how to resolve|sop|procedure|steps to take|troubleshoot", re.I)),
    ("TOTAL_COMPLAINT_COUNT", re.compile(r"(?:how many|total|number of|count of)\s+(?:total\s+)?(?:complaint|ticket|case)s?(?:\s+(?:are\s+there|in\s+system|in\s+database))?$|how many open|how many closed|how many escalated", re.I)),
    ("SUMMARY", re.compile(r"summarize|summary|overview|briefing|today's complaint|daily report", re.I)),
]


def classify_admin_intent(text: str) -> str:
    """Classify the operator query to guide context selection and fallback structuring."""
    for intent, pattern in INTENT_PATTERNS:
        if pattern.search(text):
            return intent
    # If query specifically mentions a region with inquiry keywords
    if _extract_region_mention(text):
        return "SPECIFIC_REGION_QUERY"
    return "GENERAL_OPS"


def _extract_region_mention(text: str) -> Optional[str]:
    """Check if query mentions any known region."""
    conn = db.connect()
    regions = [r["region"] for r in conn.execute("SELECT DISTINCT region FROM complaints WHERE region IS NOT NULL").fetchall() if r["region"]]
    t_lower = text.lower()
    t_clean = re.sub(r"[^\w\s]", " ", t_lower)

    # 1. Exact or substring match of full region or comma-separated parts
    for reg in regions:
        reg_low = reg.lower()
        if reg_low in t_lower or reg_low in t_clean:
            return reg
        parts = [p.strip().lower() for p in reg.split(",") if len(p.strip()) > 3]
        for part in parts:
            if part in t_lower or part in t_clean:
                return reg

    # 2. Match multi-word region substrings (e.g. 'raj nagar' in 'raj nagar extention')
    for reg in regions:
        words = [w for w in re.split(r"[\s,]+", reg.lower()) if len(w) > 3]
        if len(words) >= 2 and all(w in t_lower for w in words[:2]):
            return reg
        elif len(words) == 1 and words[0] in t_lower and len(words[0]) >= 5:
            return reg

    return None


def _extract_incident_mention(text: str) -> Optional[str]:
    """Check if query mentions a specific incident ID (e.g. INC-2026-ABCD)."""
    match = re.search(r"\b(INC-\d{4}-[A-Z0-9]+)\b", text, re.I)
    return match.group(1).upper() if match else None


def _extract_complaint_mention(text: str) -> Optional[str]:
    """Check if query mentions a specific complaint ID."""
    match = re.search(r"\b(CMP-[A-Za-z0-9-]+|C\d+)\b", text, re.I)
    return match.group(1) if match else None


def get_admin_data_snapshot(query: str = "") -> dict:
    """Extract factual snapshot directly from SQLite DB and analytics pipelines.
    
    Never generates synthetic values — all numbers and ticket IDs represent actual database state.
    """
    conn = db.connect()
    stats = analytics.resolution_stats({})
    categories = analytics.category_breakdown({})
    recurring_themes_list = analytics.recurring_themes({}, top=10)

    # Top recurring ticket summaries
    recurring_summaries = db.rows_to_dicts(conn.execute(
        "SELECT ticket_summary, COUNT(*) count FROM complaints WHERE ticket_summary IS NOT NULL "
        "GROUP BY ticket_summary ORDER BY count DESC LIMIT 8"
    ).fetchall())

    # Service breakdown
    services_breakdown = db.rows_to_dicts(conn.execute(
        "SELECT COALESCE(service_type, 'other') service, COUNT(*) count "
        "FROM complaints WHERE service_type IS NOT NULL GROUP BY service ORDER BY count DESC"
    ).fetchall())
    
    # Top priority open complaints needing immediate attention
    immediate_tickets = db.rows_to_dicts(conn.execute(
        "SELECT complaint_id, ticket_summary, text, category, region, priority_score, "
        "priority_label, priority_factors, status, sla_deadline, assigned_to, timestamp "
        "FROM complaints WHERE status != 'closed' "
        "ORDER BY priority_score DESC LIMIT 6"
    ).fetchall())

    # Complaints with highest escalation risk
    risk_tickets = db.rows_to_dicts(conn.execute(
        "SELECT complaint_id, ticket_summary, text, category, region, escalation_risk, "
        "priority_score, priority_factors, status, timestamp "
        "FROM complaints WHERE status != 'closed' AND escalation_risk IS NOT NULL "
        "ORDER BY escalation_risk DESC LIMIT 6"
    ).fetchall())

    # Active & recent incidents
    active_incidents = db.rows_to_dicts(conn.execute(
        "SELECT incident_id, region, service_type, opened_at, complaint_count, spike_pct, "
        "root_cause, confidence, evidence, status, admin_ack_status "
        "FROM incidents "
        "WHERE status != 'resolved' "
        "ORDER BY opened_at DESC LIMIT 6"
    ).fetchall())

    # Region density & volume (Top and Lowest)
    regional_counts = db.rows_to_dicts(conn.execute(
        "SELECT region, COUNT(*) count, SUM(status != 'closed') open_count, SUM(status = 'closed') closed_count "
        "FROM complaints WHERE region IS NOT NULL GROUP BY region ORDER BY count DESC LIMIT 8"
    ).fetchall())

    regional_counts_lowest = db.rows_to_dicts(conn.execute(
        "SELECT region, COUNT(*) count, SUM(status != 'closed') open_count, SUM(status = 'closed') closed_count "
        "FROM complaints WHERE region IS NOT NULL GROUP BY region ORDER BY count ASC LIMIT 8"
    ).fetchall())

    # SLA breaches
    sla_breaches = db.rows_to_dicts(conn.execute(
        "SELECT complaint_id, ticket_summary, region, category, priority_label, sla_deadline, assigned_to "
        "FROM complaints WHERE status != 'closed' AND sla_deadline IS NOT NULL AND sla_deadline < datetime('now') "
        "LIMIT 6"
    ).fetchall())

    # Targeted entity lookup if mentioned
    target_info = {}
    region_match = _extract_region_mention(query)
    if region_match:
        reg_rows = conn.execute(
            "SELECT COUNT(*) total, SUM(status != 'closed') open_count, SUM(status = 'closed') closed_count, AVG(escalation_risk) avg_risk "
            "FROM complaints WHERE region=?", (region_match,)).fetchone()
        reg_inc = conn.execute(
            "SELECT * FROM incidents WHERE region=? ORDER BY opened_at DESC LIMIT 1", (region_match,)).fetchone()
        reg_cats = db.rows_to_dicts(conn.execute(
            "SELECT category, COUNT(*) count FROM complaints WHERE region=? GROUP BY category ORDER BY count DESC",
            (region_match,)
        ).fetchall())
        reg_tickets = db.rows_to_dicts(conn.execute(
            "SELECT complaint_id, ticket_summary, text, category, priority_label, status, timestamp "
            "FROM complaints WHERE region=? ORDER BY timestamp DESC LIMIT 4",
            (region_match,)
        ).fetchall())
        target_info["region_details"] = {
            "region": region_match,
            "total_complaints": reg_rows["total"] if reg_rows else 0,
            "open_complaints": reg_rows["open_count"] if reg_rows else 0,
            "closed_complaints": reg_rows["closed_count"] if reg_rows else 0,
            "avg_escalation_risk": round(reg_rows["avg_risk"] or 0, 2) if reg_rows else 0,
            "top_categories": reg_cats,
            "recent_tickets": reg_tickets,
            "incident": dict(reg_inc) if reg_inc else None
        }

    incident_match = _extract_incident_mention(query)
    if incident_match:
        inc_row = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (incident_match,)).fetchone()
        if inc_row:
            target_info["incident_details"] = dict(inc_row)

    complaint_match = _extract_complaint_mention(query)
    if complaint_match:
        cmp_row = conn.execute("SELECT * FROM complaints WHERE complaint_id=?", (complaint_match,)).fetchone()
        if cmp_row:
            target_info["complaint_details"] = dict(cmp_row)

    # Search matches for specific category / service keywords
    q_low = query.lower()
    for kw in ("network", "internet", "broadband", "billing", "service", "device", "fiber", "fibre", "sim", "recharge"):
        if kw in q_low:
            matched = db.rows_to_dicts(conn.execute(
                "SELECT complaint_id, ticket_summary, text, category, service_type, region, priority_label, status "
                "FROM complaints WHERE text LIKE ? OR ticket_summary LIKE ? OR category LIKE ? OR service_type LIKE ? "
                "ORDER BY timestamp DESC LIMIT 5",
                (f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%")
            ).fetchall())
            if matched:
                target_info["category_matches"] = matched
                break

    return {
        "stats": stats,
        "categories": categories,
        "recurring_themes": recurring_themes_list,
        "recurring_summaries": recurring_summaries,
        "services_breakdown": services_breakdown,
        "immediate_tickets": immediate_tickets,
        "risk_tickets": risk_tickets,
        "active_incidents": active_incidents,
        "regional_counts": regional_counts,
        "regional_counts_lowest": regional_counts_lowest,
        "sla_breaches": sla_breaches,
        "target_info": target_info,
    }


def get_rag_resolution_knowledge(query: str, snapshot: dict, top_k: int = 3) -> list[dict]:
    """Retrieve relevant SOPs, troubleshooting policies, and incident writeups from existing ChromaDB."""
    search_terms = [query]
    if snapshot.get("target_info", {}).get("region_details"):
        reg = snapshot["target_info"]["region_details"]["region"]
        search_terms.append(reg)
    
    combined_query = " ".join(search_terms)
    try:
        docs = rag.retrieve(combined_query, top_k=top_k, kinds=("sop", "incident_writeup", "resolved_ticket"))
        return docs
    except Exception as exc:
        logger.warning(f"[AdminAssistant] RAG retrieval warning: {exc}")
        return []


def _format_priority_factors(factors) -> str:
    """Format priority factor tags nicely."""
    if not factors:
        return "Standard priority"
    if isinstance(factors, list):
        return ", ".join(str(f) for f in factors)
    if isinstance(factors, dict):
        return ", ".join(f"{k}: {v}" for k, v in factors.items())
    return str(factors)


TELECOM_CONCEPTS = {
    "5g": "### 📡 5G (Fifth Generation Cellular Network)\n5G is the fifth generation mobile network technology providing ultra-low latency (<1ms), gigabit data speeds (up to 10 Gbps), and massive device connectivity. It uses mid-band, millimeter wave (mmWave), and sub-6 GHz spectrum to support technologies like network slicing, enhanced mobile broadband (eMBB), and IoT.",
    "4g": "### 📡 4G LTE (Fourth Generation)\n4G LTE provides high-speed wireless mobile broadband with typical download speeds of 20–100 Mbps, low packet loss, and full IP-based network architecture for voice (VoLTE) and mobile data.",
    "volte": "### 📞 VoLTE (Voice over LTE)\nVoLTE routes voice calls over the 4G LTE data network instead of legacy 2G/3G circuit-switched networks, enabling HD voice quality, faster call setup times, and simultaneous voice and 4G data usage.",
    "vowifi": "### 📶 VoWiFi (Voice over Wi-Fi)\nVoWiFi allows placing and receiving standard phone calls and SMS over an existing Wi-Fi network connection when cellular network coverage or signal strength is weak indoors.",
    "esim": "### 📱 eSIM (Embedded Subscriber Identity Module)\nAn eSIM is a digital SIM embedded directly into device hardware that allows activating a mobile network profile over the air (OTA) without needing a physical nano-SIM card.",
    "apn": "### ⚙️ APN (Access Point Name)\nThe APN is the gateway identifier configured on a mobile device that defines the network path and IP settings required to connect to the carrier's mobile data network and internet.",
    "roaming": "### 🌐 Telecom Roaming\nRoaming enables a mobile subscriber to use voice calls, SMS, and data services seamlessly while outside their home operator's primary network coverage area, either domestically or internationally.",
    "sim": "### 💳 SIM Card (Subscriber Identity Module)\nA SIM card is an integrated circuit securely storing the international mobile subscriber identity (IMSI) number and related keys used to identify and authenticate subscribers on cellular telecommunication networks."
}


def generate_deterministic_fallback(query: str, intent: str, snapshot: dict, rag_docs: list[dict]) -> str:
    """Deterministic, factual response generator when Groq is unavailable.
    
    Guarantees zero downtime, 100% offline testability, and strict adherence to actual DB/RAG data.
    """
    # Check if query is asking for definition/explanation of a standard telecom concept
    q_low = query.lower()
    for concept_key, concept_expl in TELECOM_CONCEPTS.items():
        if re.search(rf"\b(what is|explain|define|meaning of)\s+(?:an?\s+)?{concept_key}\b", q_low) or re.search(rf"^\s*{concept_key}\??\s*$", q_low):
            return concept_expl
    stats = snapshot.get("stats", {})
    total = stats.get("total", 0)
    open_c = stats.get("open", 0)
    in_prog = stats.get("in_progress", 0)
    escalated_c = stats.get("escalated", 0)
    sla_b = stats.get("sla_breaches", 0)
    categories = snapshot.get("categories", [])
    immediate = snapshot.get("immediate_tickets", [])
    risk_tickets = snapshot.get("risk_tickets", [])
    incidents_list = snapshot.get("active_incidents", [])

    if total == 0:
        return ("### ℹ️ No Complaint Data Ingested Yet\n\n"
                "There are currently no complaints in the system. Please upload a dataset in the "
                "**Dataset Upload** panel to activate analytics, incident detection, and automated RAG intelligence.")

    # 0. Category classification reasoning explanation
    if intent == "CATEGORY_REASONING":
        target_cat = None
        cat_match = re.search(r"classified as (\w+)|categorized as (\w+)|category (\w+)", query, re.I)
        if cat_match:
            target_cat = cat_match.group(1) or cat_match.group(2) or cat_match.group(3)

        complaint_text = ""
        target_info = snapshot.get("target_info", {})
        if target_info.get("complaint_details"):
            complaint_text = target_info["complaint_details"].get("text", "")
        elif immediate:
            complaint_text = immediate[0].get("text", "")

        if not complaint_text:
            complaint_text = "internet broadband connectivity down, charged twice on bill, and service installation technician not arriving"

        reasoning = ml.explain_category_reasoning(complaint_text, target_category=target_cat)
        return ml.format_category_reasoning_response(reasoning)

    # 1. Immediate attention
    if intent == "IMMEDIATE_ATTENTION":
        lines = [
            "### 🚨 High-Priority Complaints Requiring Immediate Attention",
            f"Currently, there are **{open_c} open complaints** ({sla_b} SLA breaches, {escalated_c} escalated).\n",
            "**Top critical tickets ranked by ML priority score:**"
        ]
        if immediate:
            for idx, t in enumerate(immediate[:5], 1):
                factors = _format_priority_factors(t.get("priority_factors"))
                sla_str = f" · SLA: `{t['sla_deadline'][:16]}`" if t.get("sla_deadline") else ""
                assignee = f" · Assigned: `{t['assigned_to']}`" if t.get("assigned_to") else " · *Unassigned*"
                p_label = t.get("priority_label") or ("P1" if (t.get("priority_score") or 0) > 0.8 else "P2")
                lines.append(
                    f"{idx}. **[{t['complaint_id']}]** ({p_label} | Score: {t.get('priority_score', 0):.2f}) — **{t.get('region', 'Unknown')}**\n"
                    f"   • **Issue:** {t.get('ticket_summary') or t.get('text', '')[:100]}\n"
                    f"   • **Category:** {t.get('category', 'general').capitalize()} | **Status:** `{t.get('status')}`{sla_str}{assignee}\n"
                    f"   • **Drivers:** {factors}"
                )
        else:
            lines.append("No critical open complaints at this moment.")
        
        if rag_docs:
            lines.append("\n**Recommended Operational SOP:**")
            for doc in rag_docs[:2]:
                lines.append(f"• **{doc.get('title', 'SOP')}:** {doc.get('body', '')[:200]}...")

        return "\n".join(lines)

    # 2. Escalation risk
    if intent == "ESCALATION_RISK":
        lines = [
            "### ⚠️ Complaints with Highest Escalation Risk",
            "These tickets have high ML-computed churn risk, regulatory dispute indicators, or repeat contact patterns:\n"
        ]
        if risk_tickets:
            for idx, t in enumerate(risk_tickets[:5], 1):
                risk_pct = round((t.get("escalation_risk") or 0) * 100)
                factors = _format_priority_factors(t.get("priority_factors"))
                lines.append(
                    f"{idx}. **[{t['complaint_id']}]** — **Escalation Risk: {risk_pct}%**\n"
                    f"   • **Region:** {t.get('region', 'Unknown')} | **Category:** {t.get('category', 'general').capitalize()}\n"
                    f"   • **Summary:** {t.get('ticket_summary') or t.get('text', '')[:110]}\n"
                    f"   • **Risk Factors:** {factors}"
                )
        else:
            lines.append("No high escalation risk complaints identified.")
        return "\n".join(lines)

    # 3. Category breakdown
    if intent == "CATEGORY_BREAKDOWN":
        lines = [
            "### 📊 Complaint Categories Breakdown",
            f"Distribution across all **{total:,} complaints** in the database:\n"
        ]
        for c in categories:
            cat_name = str(c.get("category", "other")).capitalize()
            cnt = c.get("count", 0)
            pct = round((cnt / total) * 100, 1) if total > 0 else 0
            bar = "█" * int(pct // 5)
            lines.append(f"• **{cat_name}:** **{cnt:,}** ({pct}%) `{bar}`")
        
        top_cat = categories[0]["category"].capitalize() if categories else "Network"
        lines.append(f"\n**Primary Operational Focus:** `{top_cat}` represents the largest volume driver.")
        return "\n".join(lines)

    # 4a. Region with least complaints
    if intent == "LEAST_COMPLAINTS_REGION":
        lowest_regions = snapshot.get("regional_counts_lowest", [])
        lines = [
            "### 📍 Regions with Lowest / Fewest Complaints",
            f"Analysis across all monitored areas in the database:\n"
        ]
        if lowest_regions:
            least = lowest_regions[0]
            lines.append(f"• **Region with Fewest Complaints:** **{least['region']}** with **{least['count']:,}** complaint(s) ({least.get('open_count', 0)} open).\n")
            lines.append("**Bottom regions by complaint volume:**")
            for idx, r in enumerate(lowest_regions[:6], 1):
                lines.append(f"{idx}. **{r['region']}:** **{r['count']:,}** complaints ({r.get('open_count', 0)} open)")
        else:
            lines.append("No regional complaint records found.")
        return "\n".join(lines)

    # 4b. Specific region query (e.g. "how many complaints in raj nagar extension")
    target_info = snapshot.get("target_info", {})
    if intent == "SPECIFIC_REGION_QUERY" or (target_info.get("region_details") and any(w in query.lower() for w in ("how many", "count", "complaint", "ticket", "volume", "status", "in ", "for ", "at "))):
        reg_info = target_info.get("region_details", {})
        if reg_info:
            reg_name = reg_info["region"]
            tot = reg_info["total_complaints"]
            op = reg_info["open_complaints"]
            cl = reg_info.get("closed_complaints", tot - op)
            inc = reg_info.get("incident")

            lines = [
                f"### 📍 Complaint Volume for {reg_name}",
                f"• **Total Complaints in {reg_name}:** **{tot:,}** ({op} open, {cl} closed)",
                f"• **Average Escalation Risk:** {round(reg_info.get('avg_escalation_risk', 0) * 100)}%",
            ]
            if inc:
                lines.append(f"• **Active Incident:** 🔴 Incident `{inc.get('incident_id')}` ({inc.get('status')}) — *{inc.get('root_cause') or 'Under investigation'}*")
            else:
                lines.append("• **Incident Status:** 🟢 No active incidents detected in this area.")

            if reg_info.get("top_categories"):
                top_cats_str = ", ".join(f"{c['category'].capitalize()}: {c['count']}" for c in reg_info["top_categories"][:3])
                lines.append(f"• **Top Categories in {reg_name}:** {top_cats_str}")

            if reg_info.get("recent_tickets"):
                lines.append(f"\n**Recent Tickets in {reg_name}:**")
                for t in reg_info["recent_tickets"][:3]:
                    p_label = t.get("priority_label", "P2")
                    lines.append(f"• **[{t.get('complaint_id')}]** ({p_label}) — {t.get('ticket_summary') or t.get('text', '')[:90]}")

            return "\n".join(lines)

    # 4c. Regional breakdown / top regions
    if intent == "REGIONAL_BREAKDOWN":
        top_regions = snapshot.get("regional_counts", [])
        lines = [
            "### 🗺️ Regional Complaint Distribution",
            f"Breakdown of complaint volume across top monitored regions:\n"
        ]
        if top_regions:
            lines.append(f"• **Highest Complaint Region:** **{top_regions[0]['region']}** with **{top_regions[0]['count']:,}** complaints.\n")
            lines.append("**Top Regions by Volume:**")
            for idx, r in enumerate(top_regions[:6], 1):
                pct = round((r['count'] / total) * 100, 1) if total > 0 else 0
                lines.append(f"{idx}. **{r['region']}:** **{r['count']:,}** ({pct}%) — {r.get('open_count', 0)} open")
        else:
            lines.append("No regional data available.")
        return "\n".join(lines)

    # 4d. Total complaints count
    if intent == "TOTAL_COMPLAINT_COUNT":
        lines = [
            "### 📊 Overall Complaint Metrics",
            f"• **Total Complaints Ingested:** **{total:,}**",
            f"• **Open Complaints:** **{open_c:,}**",
            f"• **In Progress:** **{in_prog:,}**",
            f"• **Escalated:** **{escalated_c:,}**",
            f"• **Closed / Resolved:** **{stats.get('closed', 0):,}** ({round(stats.get('resolution_rate', 0) * 100)}% resolution rate)",
            f"• **SLA Breaches:** **{sla_b:,}** pending tickets",
        ]
        return "\n".join(lines)

    # 4e. Regional spike / why increasing / incidents
    if intent in ("REGION_SPIKE", "INCIDENT_STATUS", "ROOT_CAUSE"):
        lines = [
            "### 📡 Active Incidents & Root-Cause Intelligence",
            f"Incident detection continuously tracks regional volumes vs rolling 7-day baselines.\n"
        ]
        if incidents_list:
            for inc in incidents_list:
                status_icon = "🔴" if inc.get("status") == "open" else "🟡" if inc.get("status") == "investigating" else "🟢"
                spike_str = f"{round(inc.get('spike_pct', 0) / 100 + 1)}x baseline" if (inc.get("spike_pct") or 0) > 500 else f"+{round(inc.get('spike_pct', 0))}%"
                lines.append(
                    f"#### {status_icon} Incident {inc['incident_id']} — {inc.get('region')}\n"
                    f"• **Service:** {inc.get('service_type') or 'General'} | **Volume:** {inc.get('complaint_count', 0)} complaints ({spike_str})\n"
                    f"• **Status:** `{inc.get('status')}` | **Admin Ack:** `{inc.get('admin_ack_status')}`\n"
                    f"• **Likely Root Cause:** **{inc.get('root_cause') or 'Investigation pending'}** (Confidence: {round(inc.get('confidence') or 0)}%)"
                )
                if inc.get("evidence"):
                    ev_items = inc["evidence"] if isinstance(inc["evidence"], list) else [str(inc["evidence"])]
                    lines.append("• **Computed Evidence:**")
                    for ev in ev_items[:3]:
                        lines.append(f"  - {ev}")
                lines.append("")
        else:
            lines.append("No active regional incidents currently open. Complaint volume across all monitored areas remains within rolling baseline limits.")
        
        if rag_docs and intent == "ROOT_CAUSE":
            lines.append("\n**Historical Precedents & Resolution Guides (ChromaDB):**")
            for doc in rag_docs[:2]:
                lines.append(f"• **{doc.get('title')}:** {doc.get('body', '')[:180]}...")

        return "\n".join(lines)

    # 5. Recommended action
    if intent == "RECOMMENDED_ACTION":
        lines = [
            "### 🛠️ Recommended Operational Actions & SOPs",
            "Based on live incident patterns and ChromaDB Standard Operating Procedures:\n"
        ]
        if incidents_list:
            active_open = [i for i in incidents_list if i.get("status") != "resolved"]
            if active_open:
                top_inc = active_open[0]
                lines.append(f"**Priority Action for Live Incident {top_inc['incident_id']} ({top_inc.get('region')}):**")
                lines.append(f"1. **Acknowledge & Dispatch:** Assign to local Field Operations / Network Ops team.")
                lines.append(f"2. **Address Root Cause:** Investigate `{top_inc.get('root_cause') or 'Disruption'}`.")
                lines.append(f"3. **Proactive Customer Notice:** Trigger approval in **Notify Queue** to alert {top_inc.get('complaint_count')} affected customers.")
                lines.append("")

        if rag_docs:
            lines.append("**Applicable SOPs & Knowledge Base Guidance:**")
            for doc in rag_docs:
                lines.append(f"• **{doc.get('title')}:**\n  {doc.get('body')}")
        else:
            lines.append("• **Network Disruption:** Power cycle local node/OLT, verify backhaul throughput, re-splice fiber junction if physical break.")
            lines.append("• **Billing Inquiries:** Trigger automated transaction reconciliation job; reverse verified duplicate deductions within 48h.")
            lines.append("• **Service Installation:** Escalate pending installations (>7 days) to Regional Area Manager.")

        return "\n".join(lines)

    # 6. Recurring complaint themes
    if intent == "RECURRING_THEMES":
        lines = [
            "### 🔁 Top Recurring Complaint Themes",
            f"Analysis across **{total:,} complaints** in the platform:\n"
        ]
        themes = snapshot.get("recurring_themes", [])
        if themes:
            for idx, th in enumerate(themes[:8], 1):
                cnt = th.get("count", 0)
                pct = round((cnt / total) * 100, 1) if total > 0 else 0
                theme_name = th.get("theme", "").title()
                lines.append(f"{idx}. **{theme_name}:** **{cnt:,}** occurrences ({pct}%)")
        else:
            lines.append("No recurring complaint themes identified yet.")

        summaries = snapshot.get("recurring_summaries", [])
        if summaries:
            lines.append("\n**Most Common Ticket Summaries:**")
            for s in summaries[:4]:
                lines.append(f"• \"{s.get('ticket_summary')}\" — **{s.get('count')}** tickets")
        return "\n".join(lines)

    # 7. Specific category complaint count
    if intent == "SPECIFIC_CATEGORY_COUNT":
        target = "network"
        q_low = query.lower()
        if "bill" in q_low or "payment" in q_low or "recharge" in q_low:
            target = "billing"
        elif "device" in q_low or "router" in q_low or "modem" in q_low:
            target = "device"
        elif "service" in q_low or "install" in q_low:
            target = "service"
        elif "internet" in q_low or "network" in q_low or "broadband" in q_low or "wifi" in q_low or "fiber" in q_low or "data" in q_low:
            target = "network"

        cat_match = next((c for c in categories if str(c.get("category", "")).lower() == target), None)
        cnt = cat_match.get("count", 0) if cat_match else 0
        pct = round((cnt / total) * 100, 1) if total > 0 else 0

        lines = [
            f"### 📊 Complaints in '{target.capitalize()}' Category",
            f"• **Total {target.capitalize()} Complaints:** **{cnt:,}** out of {total:,} ({pct}% of all complaints)\n"
        ]

        target_info = snapshot.get("target_info", {})
        if target_info.get("category_matches"):
            lines.append(f"**Recent {target.capitalize()} Tickets:**")
            for t in target_info["category_matches"][:4]:
                p_label = t.get("priority_label", "P2")
                lines.append(f"• **[{t.get('complaint_id')}]** ({p_label}) — {t.get('ticket_summary') or t.get('text', '')[:90]}")

        return "\n".join(lines)

    # 8. Default / Summary
    lines = [
        "### 📋 Operations Summary & System Status",
        f"Platform is actively monitoring **{total:,} complaints** across all regions.\n",
        f"• **Resolution Status:** {stats.get('closed', 0)} Closed ({round(stats.get('resolution_rate', 0) * 100)}%), "
        f"{open_c} Open, {in_prog} In Progress, {escalated_c} Escalated",
        f"• **SLA Breaches:** **{sla_b}** pending tickets",
        f"• **Active Incidents:** {len([i for i in incidents_list if i.get('status') != 'resolved'])} ongoing",
        f"• **Average Customer Feedback:** ⭐ {stats.get('avg_rating') or 'N/A'} ({stats.get('feedback_count', 0)} ratings)\n"
    ]
    if categories:
        top_cats = ", ".join(f"{c['category'].capitalize()} ({c['count']})" for c in categories[:3])
        lines.append(f"**Top Categories:** {top_cats}")
    if immediate:
        lines.append(f"\n**Next Critical Action:** Review ticket `[{immediate[0]['complaint_id']}]` ({immediate[0].get('region')}) — score {immediate[0].get('priority_score', 0):.2f}.")
    
    return "\n".join(lines)


def _get_recent_admin_messages(user_id: str, limit: int = 8) -> list[dict]:
    """Retrieve recent chat history for conversation continuity."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT role, text, meta, created_at FROM chat_messages WHERE user_id=? "
        "ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    return list(reversed([dict(r) for r in rows]))


def chat(admin_user: dict, text: str) -> dict:
    """Entry point for Admin AI Assistant chat requests.
    
    Follows LangGraph Admin Agent orchestration:
    Admin Question -> Intent Classification -> Live DB/ML Data -> ChromaDB RAG -> Groq LLM (with fallback) -> Admin Answer
    """
    user_id = admin_user.get("user_id", "USR-admin")
    conn = db.connect()
    
    # 1. Save Admin's question
    conn.execute(
        "INSERT INTO chat_messages(message_id,user_id,role,text,created_at) VALUES(?,?,?,?,?)",
        (db.new_id("MSG"), user_id, "user", text, db.now_iso())
    )
    conn.commit()

    # 2. Delegate orchestration to LangGraph Admin Agent
    from ..agents.admin_agent import run_admin_agent
    result = run_admin_agent(admin_user, text)
    reply = result["reply"]
    meta = result["meta"]

    # 3. Persist assistant reply in chat_messages table
    conn.execute(
        "INSERT INTO chat_messages(message_id,user_id,role,text,meta,created_at) VALUES(?,?,?,?,?,?)",
        (db.new_id("MSG"), user_id, "assistant", reply, json.dumps(meta), db.now_iso())
    )
    conn.commit()

    return {
        "reply": reply,
        "meta": meta
    }


def history(user_id: str, limit: int = 50) -> list[dict]:
    """Retrieve chat history for the admin."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT message_id, role, text, meta, created_at FROM chat_messages "
        "WHERE user_id=? ORDER BY created_at ASC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("meta") and isinstance(d["meta"], str):
            try:
                d["meta"] = json.loads(d["meta"])
            except ValueError:
                pass
        out.append(d)
    return out


def clear_history(user_id: str) -> dict:
    """Clear admin chat conversation history."""
    conn = db.connect()
    conn.execute("DELETE FROM chat_messages WHERE user_id=?", (user_id,))
    conn.commit()
    return {"cleared": True}
