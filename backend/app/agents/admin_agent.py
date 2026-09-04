"""LangGraph-based Admin Operations Agent for TelConnect.

Orchestrates the grounded Telecom Admin Operations workflow using LangGraph StateGraph:
1. classify_intent: Classifies the admin inquiry into operational intents
2. collect_live_data: Extracts factual snapshot from SQLite DB and analytics pipelines
3. retrieve_rag: Retrieves relevant SOPs, troubleshooting guides, and incident writeups from ChromaDB
4. generate_response: Synthesizes grounded executive response via Groq LLM with deterministic offline fallback
"""
import json
import logging
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from ..controllers import admin_assistant
from ..services.groq_client import groq_available, groq_chat_messages
from ..services.telecom_filter import is_telecom_related, TELECOM_RESTRICTION_MESSAGE

logger = logging.getLogger(__name__)


class AdminAgentState(TypedDict):
    admin_user: dict
    raw_query: str
    intent: str
    snapshot: dict
    rag_docs: list[dict]
    fallback_answer: str
    response: str
    source: str
    meta: dict
    steps: list[str]


def node_classify_intent(state: AdminAgentState) -> dict:
    """Classify the operator inquiry into operational intent."""
    query = state["raw_query"]
    intent = admin_assistant.classify_admin_intent(query)
    steps = state.get("steps", []) + ["classify_intent"]
    return {
        "intent": intent,
        "steps": steps,
    }


def node_collect_live_data(state: AdminAgentState) -> dict:
    """Gather live factual data snapshot from SQLite database and analytics."""
    query = state["raw_query"]
    snapshot = admin_assistant.get_admin_data_snapshot(query)
    steps = state.get("steps", []) + ["collect_live_data"]
    return {
        "snapshot": snapshot,
        "steps": steps,
    }


def node_retrieve_rag(state: AdminAgentState) -> dict:
    """Retrieve relevant SOPs, incident writeups, and resolution knowledge from ChromaDB."""
    query = state["raw_query"]
    snapshot = state.get("snapshot", {})
    rag_docs = admin_assistant.get_rag_resolution_knowledge(query, snapshot, top_k=3)
    steps = state.get("steps", []) + ["retrieve_rag"]
    return {
        "rag_docs": rag_docs,
        "steps": steps,
    }


def node_generate_response(state: AdminAgentState) -> dict:
    """Generate grounded response via Groq LLM with deterministic offline fallback."""
    query = state["raw_query"]
    intent = state.get("intent", "GENERAL_OPS")
    snapshot = state.get("snapshot", {})
    rag_docs = state.get("rag_docs", [])
    admin_user = state.get("admin_user", {})
    user_id = admin_user.get("user_id", "USR-admin")

    # 1. Compute deterministic fallback
    fallback_answer = admin_assistant.generate_deterministic_fallback(query, intent, snapshot, rag_docs)

    reply = fallback_answer
    source = "offline_fallback"

    if intent == "CATEGORY_REASONING":
        reply = fallback_answer
        source = "category_reasoning_engine"
    elif groq_available():
        try:
            recent = admin_assistant._get_recent_admin_messages(user_id, limit=6)

            # Format live database snapshot for LLM context
            stats = snapshot.get("stats", {})
            active_inc_summary = [
                {
                    "id": inc["incident_id"],
                    "region": inc["region"],
                    "service": inc.get("service_type"),
                    "complaints": inc["complaint_count"],
                    "spike": inc.get("spike_pct"),
                    "root_cause": inc.get("root_cause"),
                    "confidence": inc.get("confidence"),
                    "status": inc.get("status"),
                }
                for inc in snapshot.get("active_incidents", [])
            ]

            immediate_summary = [
                {
                    "id": t["complaint_id"],
                    "region": t.get("region"),
                    "category": t.get("category"),
                    "summary": t.get("ticket_summary") or t.get("text", "")[:120],
                    "priority_score": t.get("priority_score"),
                    "priority_label": t.get("priority_label"),
                    "factors": t.get("priority_factors"),
                    "sla": t.get("sla_deadline"),
                }
                for t in snapshot.get("immediate_tickets", [])[:5]
            ]

            rag_context_text = "\n".join(
                f"- [{d.get('title', 'SOP')} ({d.get('kind', 'kb')} - similarity {d.get('similarity', 0)})]: {d.get('body')}"
                for d in rag_docs
            )

            system_prompt = (
                "You are the Telecom Operations AI Assistant for TelConnect Network Operations Center (NOC) and Support Admins.\n"
                "You are a telecom-focused assistant. Answer only questions related to telecommunications and telecom services. "
                "If a user's question is unrelated to telecommunications, do not answer the question. Politely explain that you can only assist with telecom-related topics.\n\n"
                "Provide executive, direct, concise, and structured operational intelligence grounded STRICTLY in the provided platform data.\n\n"
                "CRITICAL OPERATIONAL RULES:\n"
                "1. Direct Answer: Answer the admin's specific question directly:\n"
                "   - If asked for the region with least / fewest / lowest complaints, state the lowest-volume region(s) with their exact complaint count from the Lowest Regions data.\n"
                "   - If asked how many complaints are in a specific region (e.g. Raj Nagar, Delhi, Ghaziabad), state the exact total and open complaint count for that region from Targeted Entity / Region Details.\n"
                "   - If asked for the most recurring complaints / themes, state the top recurring themes and counts.\n"
                "   - If asked for count of internet / network / billing / service complaints, provide the exact numbers from Category Breakdown.\n"
                "   - If asked for highest complaint region or regional breakdown, state the top regions from Top Regional Hotspots.\n"
                "   - If asked for overall metrics or general summary, provide direct figures and an executive briefing.\n"
                "2. Base all complaint counts, category metrics, recurring themes, incident statuses, SLA breaches, root causes, and ticket IDs ONLY on the provided Live Database Snapshot.\n"
                "3. Never fabricate ticket numbers, statistics, or metrics not present in the data.\n"
                "4. For resolution steps, troubleshooting, or recommended actions, synthesize the ChromaDB SOPs and past incident writeups.\n"
                "5. Format responses cleanly with Markdown headers (###), bullet points, and bold text for key metrics.\n"
                "6. When explaining category classification reasoning, always structure as:\n"
                "   Primary Category: <Category>\n\n"
                "   Evidence:\n"
                "   - <evidence token 1>\n"
                "   - <evidence token 2>\n\n"
                "   Related Categories:\n"
                "   - <Related Category 1>\n"
                "   - <Related Category 2>"
            )

            recurring_themes_summary = snapshot.get("recurring_themes", [])[:8]
            services_summary = snapshot.get("services_breakdown", [])[:6]
            recurring_summaries_list = snapshot.get("recurring_summaries", [])[:5]

            user_context = (
                f"ADMIN QUESTION: {query}\n\n"
                f"LIVE DATABASE SNAPSHOT:\n"
                f"• Total Complaints: {stats.get('total')}, Open: {stats.get('open')}, In Progress: {stats.get('in_progress')}, Closed: {stats.get('closed')}\n"
                f"• SLA Breaches: {stats.get('sla_breaches')}, Escalated: {stats.get('escalated')}\n"
                f"• Category Breakdown: {json.dumps(snapshot.get('categories', []))}\n"
                f"• Service Types Breakdown: {json.dumps(services_summary)}\n"
                f"• Top Recurring Complaint Themes: {json.dumps(recurring_themes_summary)}\n"
                f"• Common Complaint Summaries: {json.dumps(recurring_summaries_list)}\n"
                f"• Active Incidents: {json.dumps(active_inc_summary)}\n"
                f"• Top Immediate Priority Tickets: {json.dumps(immediate_summary)}\n"
                f"• Top Regional Hotspots (Highest Volume): {json.dumps(snapshot.get('regional_counts', []))}\n"
                f"• Lowest Regions (Fewest Complaints): {json.dumps(snapshot.get('regional_counts_lowest', []))}\n"
            )
            if snapshot.get("target_info"):
                user_context += f"• Targeted Entity / Region Details / Matches: {json.dumps(snapshot['target_info'])}\n"

            if rag_context_text:
                user_context += f"\nRETRIEVED SOPs & RESOLUTION KNOWLEDGE (ChromaDB):\n{rag_context_text}\n"

            llm_messages = [
                {"role": "system", "content": system_prompt},
                *([{"role": m["role"], "content": m["text"]} for m in recent[:-1]]),
                {"role": "user", "content": user_context},
            ]

            llm_reply = groq_chat_messages(llm_messages, fallback=fallback_answer, max_tokens=700, temperature=0.2)
            if llm_reply and len(llm_reply.strip()) > 20:
                reply = llm_reply
                source = "groq_live"
        except Exception as exc:
            logger.warning(f"[AdminAgent] Groq chat exception: {exc}")
            reply = fallback_answer
            source = "offline_fallback"

    meta = {
        "intent": intent,
        "source": source,
        "groq_live": groq_available(),
        "retrieved_docs_count": len(rag_docs),
        "docs": [{"title": d.get("title"), "kind": d.get("kind"), "similarity": d.get("similarity")} for d in rag_docs],
    }

    steps = state.get("steps", []) + ["generate_response"]

    return {
        "fallback_answer": fallback_answer,
        "response": reply,
        "source": source,
        "meta": meta,
        "steps": steps,
    }


def build_admin_agent_graph():
    """Build and compile the LangGraph StateGraph workflow for Admin Operations."""
    graph = StateGraph(AdminAgentState)
    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("collect_live_data", node_collect_live_data)
    graph.add_node("retrieve_rag", node_retrieve_rag)
    graph.add_node("generate_response", node_generate_response)

    # Wire sequential execution flow
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "collect_live_data")
    graph.add_edge("collect_live_data", "retrieve_rag")
    graph.add_edge("retrieve_rag", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


_admin_graph_runnable = None


def get_admin_agent_graph():
    """Get or lazily initialize the singleton compiled Admin LangGraph."""
    global _admin_graph_runnable
    if _admin_graph_runnable is None:
        _admin_graph_runnable = build_admin_agent_graph()
    return _admin_graph_runnable


def run_admin_agent(admin_user: dict, text: str) -> dict:
    """Execute the LangGraph Admin Agent workflow for an admin query."""
    if not is_telecom_related(text, is_admin=True):
        return {
            "reply": TELECOM_RESTRICTION_MESSAGE,
            "meta": {
                "intent": "RESTRICTED_NON_TELECOM",
                "source": "domain_filter",
                "groq_live": groq_available(),
                "retrieved_docs_count": 0,
                "docs": [],
            },
            "steps": ["telecom_domain_check"],
        }

    app = get_admin_agent_graph()

    initial_state: AdminAgentState = {
        "admin_user": admin_user,
        "raw_query": text,
        "intent": "GENERAL_OPS",
        "snapshot": {},
        "rag_docs": [],
        "fallback_answer": "",
        "response": "",
        "source": "offline_fallback",
        "meta": {},
        "steps": [],
    }

    result = app.invoke(initial_state)
    return {
        "reply": result["response"],
        "meta": result["meta"],
        "steps": result["steps"],
    }
