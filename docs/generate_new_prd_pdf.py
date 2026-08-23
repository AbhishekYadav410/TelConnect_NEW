"""Generate NEW_PRD.pdf matching the exact 23-page PDF template structure and styling."""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

DOCS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(DOCS_DIR)
NEW_PRD_PDF_DOCS = os.path.join(DOCS_DIR, "NEW_PRD.pdf")
NEW_PRD_PDF_ROOT = os.path.join(ROOT_DIR, "NEW_PRD.pdf")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0f766e"))

        # Running Header
        self.drawString(54, 752, "TELECOM COMPLAINT INTELLIGENCE & AUTOMATED RESOLUTION ASSISTANT")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(558, 752, "TelConnect • Cognizant Hackathon Use Case 13")

        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 744, 558, 744)

        # Running Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 32, "PRD v10.0 — Admin-Oriented Multi-Task Agent & Text-Only Intelligence")
        self.drawRightString(558, 32, f"PRD v10.0 | Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_new_prd_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0f766e")   # Teal
    secondary_color = colors.HexColor("#0f2b46") # Navy
    text_dark = colors.HexColor("#1e293b")
    text_muted = colors.HexColor("#475569")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=secondary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=primary_color,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=text_dark,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=12,
        bulletIndent=4,
        spaceAfter=2.5
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#0c4a6e")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=text_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    story = []

    def make_table(data, widths, header_color=secondary_color):
        t = Table(data, colWidths=widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    # ================= PAGE 1 =================
    story.append(Paragraph("PRODUCT REQUIREMENTS DOCUMENT", ParagraphStyle('SuperTitle', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor("#64748b"), spaceAfter=3)))
    story.append(Paragraph("Telecom Complaint Intelligence<br/>& Automated Resolution Assistant", title_style))
    story.append(Paragraph("Professional, admin-oriented product specification<br/><b>Cognizant Hackathon • Use Case 13</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=8))

    spec_data = [
        [Paragraph("Document", table_header_style), Paragraph("Specification", table_header_style)],
        [Paragraph("Version", table_cell_bold), Paragraph("10.0 — Admin-Oriented Multi-Task Agent & Text-Only Intelligence PRD", table_cell_style)],
        [Paragraph("Product Type", table_cell_bold), Paragraph("AI-powered telecom complaint intelligence and automated resolution platform", table_cell_style)],
        [Paragraph("Primary User", table_cell_bold), Paragraph("Support / Operations Admin teams", table_cell_style)],
        [Paragraph("Secondary User", table_cell_bold), Paragraph("Telecom customers", table_cell_style)],
        [Paragraph("Admin Assistant UI", table_cell_bold), Paragraph("Admin Operations Dashboard + Admin AI Assistant", table_cell_style)],
        [Paragraph("Agent Orchestration", table_cell_bold), Paragraph("LangGraph Multi-Task StateGraph (customer workflow + admin operations agent)", table_cell_style)],
        [Paragraph("Multilingual Engine", table_cell_bold), Paragraph("Hugging Face DistilBERT (multilingual-cased) + Groq translation + rule fallback", table_cell_style)],
        [Paragraph("Primary AI Provider", table_cell_bold), Paragraph("Groq API (Llama models) with deterministic offline fallbacks", table_cell_style)],
        [Paragraph("Customer Interaction", table_cell_bold), Paragraph("Text-based conversational assistant", table_cell_style)],
        [Paragraph("Core Data Store", table_cell_bold), Paragraph("SQLite (tci.db with WAL mode, foreign keys, immutable audit logs)", table_cell_style)],
        [Paragraph("Knowledge Store", table_cell_bold), Paragraph("ChromaDB persistent vector store + Sentence Transformers (all-MiniLM-L6-v2)", table_cell_style)],
        [Paragraph("Geolocation Engine", table_cell_bold), Paragraph("Geoapify Geocoding API with caching and India boundary validation", table_cell_style)],
        [Paragraph("Core Backend", table_cell_bold), Paragraph("Python + FastAPI + Uvicorn", table_cell_style)],
        [Paragraph("UI", table_cell_bold), Paragraph("Admin Operations Dashboard + Admin AI Assistant + Customer Assistant (40/60 Split) + Theme Engine (Dark/Light)", table_cell_style)],
    ]
    story.append(make_table(spec_data, [110, 394], header_color=primary_color))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Product Vision", h2_style))
    vision_text = (
        "Give telecom operations teams a single intelligence and control plane to monitor complaints, manage tickets, "
        "investigate incidents, use AI-assisted recommendations, detect service-wide patterns, approve proactive actions, "
        "and verify that customer-facing resolution outcomes are achieved.<br/><br/>"
        "The customer assistant remains the connected service channel, while the product is positioned around the admin control plane: "
        "operational visibility, queue management, incident intelligence, auditability and AI decision support."
    )
    story.append(Paragraph(vision_text, body_style))
    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("1. Product Overview", h1_style))
    story.append(Paragraph(
        "TelConnect is an admin-oriented telecom complaint intelligence and resolution platform. The Admin Dashboard is the primary "
        "operational control plane used to manage the complaint lifecycle, investigate patterns, monitor service issues, update ticket states, "
        "manage incidents, evaluate AI recommendations and query operational intelligence.", body_style))
    story.append(Paragraph(
        "The customer assistant is the connected text-based service channel: it captures complaints, diagnostics and customer confirmation "
        "while feeding authoritative operational data into the admin workflow.", body_style))
    
    story.append(Paragraph("1.1 Product Principles", h2_style))
    story.append(Paragraph("• <b>Admin first:</b> The primary workflow starts with operational visibility and ends with a controlled, auditable action or verified outcome.", bullet_style))
    story.append(Paragraph("• <b>Operational control:</b> Admins manage queues, tickets, assignments, incidents, alerts, notifications and resolution actions from one dashboard.", bullet_style))
    story.append(Paragraph("• <b>AI-assisted decisions:</b> The Admin AI Assistant provides evidence, SOP knowledge, live database context and explainable recommendations; privileged actions remain backend-controlled.", bullet_style))
    story.append(Paragraph("• <b>Customer outcome:</b> Admin actions are measured by whether complaints are resolved, tracked and confirmed by the customer.", bullet_style))
    story.append(Paragraph("• <b>One source of truth:</b> Admin dashboard and customer assistant use the same backend and SQLite operational database.", bullet_style))
    story.append(Paragraph("• <b>Dynamic by design:</b> Runtime complaints, assignments and incidents are database-driven; seed CSV data is not the live source of truth.", bullet_style))
    story.append(Paragraph("• <b>Closed loop:</b> Resolution is not final until the customer confirms it; rejected fixes reopen or escalate.", bullet_style))
    story.append(Paragraph("• <b>Explainable and auditable:</b> Priority, escalation, root-cause and AI recommendations expose evidence, while privileged actions are logged.", bullet_style))
    story.append(Paragraph("• <b>Zero-cost and offline resilient:</b> Core ticket/status operations remain usable with deterministic fallbacks when external AI services are unavailable.", bullet_style))

    story.append(Paragraph("1.2 Problem Statement", h2_style))
    story.append(Paragraph(
        "Telecom operators receive large complaint volumes across network, broadband, billing and service issues. Manual triage, "
        "fragmented ticket handling and delayed outage recognition make it difficult for operations teams to understand what is happening, "
        "which customers are affected, what should be done next and whether the customer was actually helped.", body_style))
    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("2. Objectives", h1_style))
    obj_data = [
        [Paragraph("Admin Objective", table_header_style), Paragraph("Expected Operational Outcome", table_header_style)],
        [Paragraph("Operational overview", table_cell_bold), Paragraph("Monitor complaint volume, open tickets, priorities, SLA risk, incidents and trends from one control plane.", table_cell_style)],
        [Paragraph("Queue & ticket efficiency", table_cell_bold), Paragraph("Search, filter, assign, update, escalate and resolve complaints with full status history.", table_cell_style)],
        [Paragraph("Incident intelligence", table_cell_bold), Paragraph("Detect spikes, link complaints to incidents and investigate service-wide impact.", table_cell_style)],
        [Paragraph("AI decision support", table_cell_bold), Paragraph("Use the Admin AI Assistant with live DB snapshots, ChromaDB SOPs and explainable recommendations.", table_cell_style)],
        [Paragraph("Root-cause investigation", table_cell_bold), Paragraph("Combine complaint patterns, geography, history and knowledge evidence into actionable hypotheses.", table_cell_style)],
        [Paragraph("Proactive operations", table_cell_bold), Paragraph("Review and approve customer notifications for confirmed incidents and meaningful ticket events.", table_cell_style)],
        [Paragraph("Audit & governance", table_cell_bold), Paragraph("Keep privileged actions, assignments, status changes and notification decisions traceable.", table_cell_style)],
        [Paragraph("Customer resolution outcome", table_cell_bold), Paragraph("Ensure the operational workflow ultimately produces verified customer resolution or proper escalation.", table_cell_style)],
        [Paragraph("Customer-facing assistance", table_cell_bold), Paragraph("Provide text chat, diagnostics, troubleshooting, ticket tracking and confirmation as the service channel.", table_cell_style)],
    ]
    story.append(make_table(obj_data, [130, 374]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Success Criteria", h2_style))
    story.append(Paragraph("• Admin can see complaint volume, priority, category, sentiment, escalation risk, geographic spikes, incidents and SLA information.", bullet_style))
    story.append(Paragraph("• Admin can assign, update, escalate and resolve tickets while preserving immutable status history.", bullet_style))
    story.append(Paragraph("• Admin can investigate a spike and obtain evidence-backed root-cause signals.", bullet_style))
    story.append(Paragraph("• Admin can use the Operations AI Assistant for complex operational queries without unrestricted database access.", bullet_style))
    story.append(Paragraph("• Customer outcome: every valid complaint has a persistent ticket record and can be confirmed, reopened or escalated.", bullet_style))
    story.append(Paragraph("• Resilience: ticket and status operations remain usable when Groq is unavailable.", bullet_style))

    story.append(Paragraph("2.2 Scope Boundaries", h2_style))
    story.append(Paragraph("• MVP focuses on complaint intelligence, operational orchestration and resolution support; it does not directly control telecom network equipment.", bullet_style))
    story.append(Paragraph("• Real OSS/BSS integration is a future integration point; the hackathon uses simulated telemetry APIs and controlled data feeds.", bullet_style))
    story.append(Paragraph("• External SMS/push delivery is optional for MVP; in-app notifications demonstrate the workflow.", bullet_style))
    story.append(Paragraph("• The supplied complaint dataset is seed/demo data, not the live operational database.", bullet_style))
    story.append(PageBreak())

    # ================= PAGE 4 =================
    story.append(Paragraph("3. Users & Roles", h1_style))
    roles_data = [
        [Paragraph("Role", table_header_style), Paragraph("Needs", table_header_style), Paragraph("Key Capabilities", table_header_style)],
        [Paragraph("Support Admin", table_cell_bold), Paragraph("Operational control and fast resolution management.", table_cell_style), Paragraph("Queue, assignment, priority, status, notes, resolution actions, SLA monitoring, escalation, audit.", table_cell_style)],
        [Paragraph("Network Operations", table_cell_bold), Paragraph("Detect and investigate service-wide problems.", table_cell_style), Paragraph("Heatmap, spikes, incident management, root-cause investigation, affected-customer analysis, broadcast approvals.", table_cell_style)],
        [Paragraph("Operations AI User", table_cell_bold), Paragraph("Decision support for NOC/admin workflows.", table_cell_style), Paragraph("Admin AI Assistant, prompt chips, live DB snapshots, ChromaDB SOP synthesis, classification explanations.", table_cell_style)],
        [Paragraph("Customer", table_cell_bold), Paragraph("Fast help and transparent resolution status.", table_cell_style), Paragraph("Text chat assistant, diagnostics, troubleshooting, ticket tracking, confirmation, reopen and escalation.", table_cell_style)],
        [Paragraph("System / AI", table_cell_bold), Paragraph("Automated intelligence and controlled decision support.", table_cell_style), Paragraph("LangGraph agents, ML scoring, spike detection, RAG retrieval, response generation, audit logging.", table_cell_style)],
    ]
    story.append(make_table(roles_data, [90, 140, 274]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Access Control", h2_style))
    story.append(Paragraph("• Admins access operational complaint and incident data according to role.", bullet_style))
    story.append(Paragraph("• Customers access only their own profile, conversations, complaints, notifications and feedback.", bullet_style))
    story.append(Paragraph("• AI services never receive unrestricted database access; they call authorized backend functions.", bullet_style))
    story.append(Paragraph("• All privileged actions are recorded in the audit log.", bullet_style))
    story.append(Paragraph("• Admin AI recommendations remain subject to backend authorization and operational approval where required.", bullet_style))
    story.append(PageBreak())

    # ================= PAGE 5 =================
    story.append(Paragraph("4. Admin Operational Complaint Lifecycle", h1_style))
    ops_data = [
        [Paragraph("Step", table_header_style), Paragraph("Admin / System Action", table_header_style), Paragraph("Outcome", table_header_style)],
        [Paragraph("1. Monitor", table_cell_bold), Paragraph("Review dashboard, queue, alerts and complaint intelligence.", table_cell_style), Paragraph("Operational picture established.", table_cell_style)],
        [Paragraph("2. Triage", table_cell_bold), Paragraph("Inspect category, priority, sentiment, escalation risk and incident links.", table_cell_style), Paragraph("Work prioritized.", table_cell_style)],
        [Paragraph("3. Investigate", table_cell_bold), Paragraph("Use heatmap, spike detection, incident data and AI evidence.", table_cell_style), Paragraph("Likely issue scope identified.", table_cell_style)],
        [Paragraph("4. Assign", table_cell_bold), Paragraph("Route to Field Ops, RF Team, Billing, Support L2 or Network Ops.", table_cell_style), Paragraph("Ownership established.", table_cell_style)],
        [Paragraph("5. Resolve", table_cell_bold), Paragraph("Add notes, use approved SOP/RAG guidance and record resolution source.", table_cell_style), Paragraph("Resolution attempt tracked.", table_cell_style)],
        [Paragraph("6. Verify", table_cell_bold), Paragraph("Customer confirms or rejects the proposed resolution.", table_cell_style), Paragraph("Closed-loop outcome captured.", table_cell_style)],
        [Paragraph("7. Escalate/Reopen", table_cell_bold), Paragraph("Escalate or reopen when the issue is unresolved or returns.", table_cell_style), Paragraph("No silent closure.", table_cell_style)],
        [Paragraph("8. Close", table_cell_bold), Paragraph("Finalize only after confirmation and preserve complete history.", table_cell_style), Paragraph("Auditable complaint lifecycle.", table_cell_style)],
    ]
    story.append(make_table(ops_data, [85, 235, 184]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Customer Service Channel", h2_style))
    story.append(Paragraph(
        "The customer assistant feeds the same operational lifecycle. Customer steps remain: Start → Verify → Diagnose → Resolve → "
        "Confirm → Ticket → Track → Escalate → Reopen → Close. Every status transition is persisted in SQLite with actor, timestamp and reason.", body_style))

    story.append(Paragraph("4.2 Complaint Status Model", h2_style))
    story.append(Paragraph(
        "NEW → VERIFICATION_REQUIRED → VERIFIED → CLASSIFIED → DIAGNOSING → IN_PROGRESS → RESOLVED_PENDING_CONFIRMATION → CLOSED<br/>"
        "Alternative paths: WAITING_FOR_CUSTOMER, HUMAN_ESCALATION, REOPENED.", body_style))
    story.append(PageBreak())

    # ================= PAGE 6 =================
    story.append(Paragraph("5. AI Operations & Customer Assistants", h1_style))
    story.append(Paragraph("5.1 Admin AI Assistant — Primary Decision Support", h2_style))
    story.append(Paragraph(
        "The Admin AI Assistant is a workflow-driven operations agent. It answers complex operational questions using live database "
        "snapshots and ChromaDB SOP knowledge, explains complaint classifications and priority factors, summarizes incidents, and supports "
        "NOC/admin decision-making. It does not directly mutate privileged state.", body_style))

    story.append(Paragraph("5.2 Admin Assistant Capabilities", h2_style))
    story.append(Paragraph("• Queue and ticket summaries, priority and SLA explanations.", bullet_style))
    story.append(Paragraph("• Incident and spike investigation with affected-region/customer context.", bullet_style))
    story.append(Paragraph("• Root-cause evidence synthesis from structured patterns and approved knowledge.", bullet_style))
    story.append(Paragraph("• SOP retrieval and operational troubleshooting guidance.", bullet_style))
    story.append(Paragraph("• Status, assignment and escalation explanations from authoritative SQLite state.", bullet_style))
    story.append(Paragraph("• Prompt chips and guided operational queries for fast NOC/admin briefings.", bullet_style))

    story.append(Paragraph("5.3 Customer Assistant — Text Service Channel", h2_style))
    story.append(Paragraph(
        "The customer assistant handles REPORT_COMPLAINT, DIAGNOSTIC, CHECK_STATUS, TROUBLESHOOT, KNOWN_INCIDENT, "
        "CONFIRM_RESOLUTION, REJECT_RESOLUTION, REOPEN_COMPLAINT, BILLING_QUERY, ESCALATE and GENERAL_QUERY "
        "through the LangGraph customer workflow.", body_style))

    story.append(Paragraph("5.4 LangGraph Workflows", h2_style))
    story.append(Paragraph(
        "<b>Admin workflow:</b> query → retrieve live DB context → retrieve SOP/knowledge → reason → explain recommendation → authorized action when permitted.<br/>"
        "<b>Customer workflow:</b> translate_input → route_intent → retrieve_context → execute_action → synthesize_response → translate_output.", body_style))
    story.append(PageBreak())

    # ================= PAGE 7 =================
    story.append(Paragraph("6. Solution Architecture", h1_style))
    arch_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Components", table_header_style), Paragraph("Purpose", table_header_style)],
        [Paragraph("Admin Layer", table_cell_bold), Paragraph("React operations dashboard, Admin AI Assistant, Theme Engine", table_cell_style), Paragraph("Primary control plane: queue, tickets, incidents, heatmap, analytics, alerts, notifications and audit.", table_cell_style)],
        [Paragraph("Customer Layer", table_cell_bold), Paragraph("React 40/60 text chat, diagnostic cards", table_cell_style), Paragraph("Complaint reporting, diagnostics, troubleshooting, tracking and confirmation.", table_cell_style)],
        [Paragraph("API Layer", table_cell_bold), Paragraph("Python + FastAPI + Uvicorn + hashlib-based authentication", table_cell_style), Paragraph("Central business logic, authorization and deterministic actions.", table_cell_style)],
        [Paragraph("AI Orchestration", table_cell_bold), Paragraph("LangGraph Multi-Task StateGraph", table_cell_style), Paragraph("Controls multi-turn state continuation and tool execution.", table_cell_style)],
        [Paragraph("Multilingual NLP", table_cell_bold), Paragraph("Hugging Face DistilBERT (multilingual-cased)", table_cell_style), Paragraph("Tokenization, Hinglish normalization and Devanagari validation.", table_cell_style)],
        [Paragraph("ML Intelligence", table_cell_bold), Paragraph("scikit-learn (TF-IDF + Logistic Regression) + Multi-Factor Scoring", table_cell_style), Paragraph("Classification, sentiment, urgency, escalation and priority scoring.", table_cell_style)],
        [Paragraph("Vector RAG", table_cell_bold), Paragraph("ChromaDB + Sentence Transformers (all-MiniLM-L6-v2)", table_cell_style), Paragraph("Grounded troubleshooting, FAQs, SOPs and approved resolved cases.", table_cell_style)],
        [Paragraph("Generative AI", table_cell_bold), Paragraph("Groq API (Llama models) + offline fallbacks", table_cell_style), Paragraph("Conversation, summaries, explanations and root-cause narrative.", table_cell_style)],
        [Paragraph("Geolocation", table_cell_bold), Paragraph("Geoapify Geocoding API + cache", table_cell_style), Paragraph("Location coordinates for Leaflet regional heatmap.", table_cell_style)],
        [Paragraph("Operational DB", table_cell_bold), Paragraph("SQLite (tci.db with WAL mode)", table_cell_style), Paragraph("Live complaints, users, status history, incidents, notifications and audit logs.", table_cell_style)],
        [Paragraph("Analytics / Detection", table_cell_bold), Paragraph("Spike detection, heatmap, incident engine", table_cell_style), Paragraph("Proactive operational intelligence.", table_cell_style)],
    ]
    story.append(make_table(arch_data, [95, 175, 234]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.1 Data Flow", h2_style))
    story.append(Paragraph(
        "Admin/customer/API input → validation → complaint persistence → SQLite → incident/duplicate evaluation → resolution/ChromaDB "
        "RAG → ticket lifecycle → notification/analytics → feedback.<br/><br/>"
        "<b>Operational source of truth:</b> SQLite. <b>Knowledge retrieval:</b> ChromaDB. <b>Generation/reasoning:</b> Groq. "
        "The LLM cannot become the source of live ticket truth.", body_style))
    story.append(PageBreak())

    # ================= PAGE 8 =================
    story.append(Paragraph("7. Admin Operations Dashboard", h1_style))
    story.append(Paragraph("All useful admin-dashboard capabilities from the original concept are retained and organized into 16 operational modules.", body_style))
    admin_mods = [
        [Paragraph("Dashboard Module", table_header_style), Paragraph("Features & Operational Capabilities", table_header_style)],
        [Paragraph("1. Overview", table_cell_bold), Paragraph("Total complaints, open tickets, resolved/closed tickets, high-priority complaints, SLA breaches, active incidents, complaint trends.", table_cell_style)],
        [Paragraph("2. Complaint Queue", table_cell_bold), Paragraph("Search/filter by status, category, service, region, priority, sentiment, escalation risk, date and incident.", table_cell_style)],
        [Paragraph("3. Ticket Management", table_cell_bold), Paragraph("View ticket detail, customer-safe summary, category, priority, AI analysis, incident link, status, SLA, assignment and history.", table_cell_style)],
        [Paragraph("4. Assignment & Escalation", table_cell_bold), Paragraph("Assign to support team/person (Field Ops, RF Team, Billing, Support L2, Network Ops), mark waiting for customer.", table_cell_style)],
        [Paragraph("5. Resolution Management", table_cell_bold), Paragraph("Add resolution notes, propose resolution, record resolution source, move to RESOLVED_PENDING_CONFIRMATION.", table_cell_style)],
        [Paragraph("6. Status Management", table_cell_bold), Paragraph("NEW, IN_PROGRESS, WAITING_FOR_CUSTOMER, ESCALATED, RESOLVED_PENDING_CONFIRMATION, CLOSED, REOPENED.", table_cell_style)],
        [Paragraph("7. Complaint Intelligence", table_cell_bold), Paragraph("Category distribution, sentiment, urgency, escalation risk, priority distribution and recurring issue analysis.", table_cell_style)],
        [Paragraph("8. Heatmap", table_cell_bold), Paragraph("Leaflet geographic complaint density with filters and drill-down to underlying complaints (Red=Spike, Amber=Elevated, Teal=Normal).", table_cell_style)],
        [Paragraph("9. Spike Detection", table_cell_bold), Paragraph("Rolling baseline comparison, abnormal complaint volume alerts and automatic incident creation.", table_cell_style)],
        [Paragraph("10. Root-Cause Investigator", table_cell_bold), Paragraph("Likely cause, confidence bar (90%+), evidence signals (>=3 bullets), affected region/service and supporting complaint patterns.", table_cell_style)],
        [Paragraph("11. Incident Management", table_cell_bold), Paragraph("Create/acknowledge/assign/update/resolve incidents; link complaints; inspect affected customers.", table_cell_style)],
        [Paragraph("12. Proactive Alerts", table_cell_bold), Paragraph("Admin alert inbox for complaint spikes, SLA risks, active incidents and escalation risks with unread badges.", table_cell_style)],
        [Paragraph("13. Notification Center", table_cell_bold), Paragraph("Draft, review and approve incident/customer notifications; view delivery/read state for in-app notifications.", table_cell_style)],
        [Paragraph("14. Executive Analytics", table_cell_bold), Paragraph("Resolution rate, response time, escalation rate, SLA performance, category trends, duplicate complaints and customer feedback.", table_cell_style)],
        [Paragraph("15. Data Ingestion", table_cell_bold), Paragraph("Admin-only 3-step CSV upload wizard with auto-schema detection, PII redaction and pipeline triggering.", table_cell_style)],
        [Paragraph("16. Operations AI Assistant", table_cell_bold), Paragraph("LangGraph decision support agent answering complex operational queries with live DB snapshots and ChromaDB SOPs.", table_cell_style)],
    ]
    story.append(make_table(admin_mods, [125, 379]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("7.1 Dashboard Principle", h2_style))
    story.append(Paragraph("The dashboard helps an operator answer four questions quickly: <b>What is happening? Which customers are affected? What should we do? Has the customer actually been helped?</b>", body_style))
    story.append(PageBreak())

    # ================= PAGE 9 =================
    story.append(Paragraph("8. Complaint Intelligence Pipeline", h1_style))
    pipe_data = [
        [Paragraph("Capability", table_header_style), Paragraph("Input", table_header_style), Paragraph("Output", table_header_style)],
        [Paragraph("Text Classification", table_cell_bold), Paragraph("Complaint text", table_cell_style), Paragraph("Category/subcategory/service type (Macro-F1 >= 82.4%).", table_cell_style)],
        [Paragraph("Intent Detection", table_cell_bold), Paragraph("Conversation message", table_cell_style), Paragraph("Supported assistant intent (15+ categories).", table_cell_style)],
        [Paragraph("Entity Extraction", table_cell_bold), Paragraph("Complaint text", table_cell_style), Paragraph("Location, service, device, timing and issue details.", table_cell_style)],
        [Paragraph("Sentiment Analysis", table_cell_bold), Paragraph("Complaint text/conversation", table_cell_style), Paragraph("Positive/neutral/negative/critical signal.", table_cell_style)],
        [Paragraph("Urgency Detection", table_cell_bold), Paragraph("Complaint + context", table_cell_style), Paragraph("Urgency score/level (0.0 to 1.0).", table_cell_style)],
        [Paragraph("Escalation Risk", table_cell_bold), Paragraph("Complaint + history + sentiment", table_cell_style), Paragraph("Escalation probability/risk level (churn & TRAI threats).", table_cell_style)],
        [Paragraph("Priority Scoring", table_cell_bold), Paragraph("Urgency + impact + risk + incident context", table_cell_style), Paragraph("P1/P2/P3/P4 priority with contributing factor chips.", table_cell_style)],
        [Paragraph("Duplicate Detection", table_cell_bold), Paragraph("New complaint + existing complaints/incidents", table_cell_style), Paragraph("Similarity/link recommendation.", table_cell_style)],
        [Paragraph("Ticket Summary", table_cell_bold), Paragraph("Full conversation/complaint", table_cell_style), Paragraph("Concise agent-ready 1-sentence summary.", table_cell_style)],
    ]
    story.append(make_table(pipe_data, [110, 160, 234]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("8.1 Priority Example & Formula", h2_style))
    story.append(Paragraph("<b>Priority = clamp(0, 100, w1*Urgency + w2*Sentiment + w3*Escalation + w4*Incident + w5*Repeat)</b>", body_style))
    story.append(Paragraph("• <b>P1 (Critical, 80-100):</b> SLA 2 Hours — High priority alert drafted; immediate queue banner.<br/>"
                           "• <b>P2 (High, 60-79):</b> SLA 6 Hours — Routed to Tier-2 specialist queue.<br/>"
                           "• <b>P3 (Medium, 35-59):</b> SLA 24 Hours — Standard operational queue.<br/>"
                           "• <b>P4 (Low, 0-34):</b> SLA 48 Hours — General queue.<br/>"
                           "The dashboard displays the major contributing factor chips rather than only a numeric score.", body_style))
    story.append(PageBreak())

    # ================= PAGE 10 =================
    story.append(Paragraph("9. RAG-Based Automated Resolution", h1_style))
    story.append(Paragraph("RAG is used to make the assistant useful for actual resolution rather than only classification.", body_style))
    
    story.append(Paragraph("9.1 Knowledge Base", h2_style))
    story.append(Paragraph("• Telecom troubleshooting SOPs (broadband reset, ONT reconfiguration, APN settings, eSIM).", bullet_style))
    story.append(Paragraph("• FAQs and approved service guidance.", bullet_style))
    story.append(Paragraph("• Billing/service policies.", bullet_style))
    story.append(Paragraph("• Historical confirmed resolutions.", bullet_style))
    story.append(Paragraph("• Incident resolution notes and post-mortems.", bullet_style))

    story.append(Paragraph("9.2 Resolution Decision", h2_style))
    rag_dec = [
        [Paragraph("Condition", table_header_style), Paragraph("Assistant Behaviour", table_header_style)],
        [Paragraph("Known incident exists", table_cell_bold), Paragraph("Explain incident, provide available guidance and link complaint to incident where appropriate.", table_cell_style)],
        [Paragraph("Known low-risk issue + good RAG match", table_cell_bold), Paragraph("Guide customer through safe step-by-step troubleshooting SOPs.", table_cell_style)],
        [Paragraph("Insufficient knowledge", table_cell_bold), Paragraph("Ask clarification or escalate; do not hallucinate.", table_cell_style)],
        [Paragraph("Account-sensitive issue", table_cell_bold), Paragraph("Use authenticated backend data or route to human support.", table_cell_style)],
        [Paragraph("Troubleshooting succeeds", table_cell_bold), Paragraph("Ask customer to confirm resolution (Yes ✓).", table_cell_style)],
        [Paragraph("Customer rejects resolution", table_cell_bold), Paragraph("Reopen/escalate and preserve the previous attempt.", table_cell_style)],
    ]
    story.append(make_table(rag_dec, [160, 344]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("9.3 RAG Grounding Rule", h2_style))
    story.append(Paragraph(
        "<b>Every troubleshooting response should be generated from retrieved approved knowledge.</b> The assistant should not claim a cause, "
        "ETA, policy or fix that is not supported by the retrieved ChromaDB chunks or live SQLite backend state.", body_style))
    story.append(PageBreak())

    # ================= PAGE 11 =================
    story.append(Paragraph("10. Dynamic Data & Complaint Lifecycle", h1_style))
    story.append(Paragraph("The original dataset remains useful for model training/evaluation and demonstration, but runtime operation is database-driven.", body_style))
    
    data_sources = [
        [Paragraph("Data Source", table_header_style), Paragraph("Use", table_header_style)],
        [Paragraph("Historical CSV / Demo data", table_cell_bold), Paragraph("Model development, evaluation, historical analytics and seed records.", table_cell_style)],
        [Paragraph("Customer Assistant", table_cell_bold), Paragraph("Real-time complaint creation and customer interactions.", table_cell_style)],
        [Paragraph("Admin Dashboard", table_cell_bold), Paragraph("Status updates, assignments, resolution notes and incident actions.", table_cell_style)],
        [Paragraph("Dynamic Line Diagnostics", table_cell_bold), Paragraph("Real-time simulated telemetry for line speed, latency, jitter and packet loss.", table_cell_style)],
        [Paragraph("Background Detection", table_cell_bold), Paragraph("Complaint aggregation, spike detection and incident generation.", table_cell_style)],
    ]
    story.append(make_table(data_sources, [140, 364]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("10.1 Core Database Entities", h2_style))
    entities_data = [
        [Paragraph("Entity", table_header_style), Paragraph("Purpose", table_header_style)],
        [Paragraph("users", table_cell_bold), Paragraph("Customer/admin identity and role.", table_cell_style)],
        [Paragraph("complaints", table_cell_bold), Paragraph("Live complaint/ticket record with priority and SLA.", table_cell_style)],
        [Paragraph("complaint_status_history", table_cell_bold), Paragraph("Immutable status transition history.", table_cell_style)],
        [Paragraph("chat_messages", table_cell_bold), Paragraph("Conversation messages, detected intents and metadata.", table_cell_style)],
        [Paragraph("resolutions", table_cell_bold), Paragraph("Troubleshooting/resolution attempts and confirmation.", table_cell_style)],
        [Paragraph("incidents", table_cell_bold), Paragraph("Mass-service issue and root-cause information.", table_cell_style)],
        [Paragraph("notifications", table_cell_bold), Paragraph("Ticket/incident notification records.", table_cell_style)],
        [Paragraph("kb_docs", table_cell_bold), Paragraph("RAG source metadata.", table_cell_style)],
        [Paragraph("feedback", table_cell_bold), Paragraph("Customer resolution rating (1-5 stars) and comments.", table_cell_style)],
        [Paragraph("audit_logs", table_cell_bold), Paragraph("Operational/security trace.", table_cell_style)],
    ]
    story.append(make_table(entities_data, [140, 364]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("10.2 Required Complaint Fields: complaint_id, customer_id, text, category, region, lat, long, service_type, sentiment, urgency, escalation_risk, priority_score, priority_label, sla_deadline, status, incident_id, assigned_to, ticket_summary, created_at", body_style))
    story.append(PageBreak())

    # ================= PAGE 12 =================
    story.append(Paragraph("11. Verification, Status & Resolution Management", h1_style))
    story.append(Paragraph("This section addresses the most important gap in a basic chatbot: what happens after the customer reports the issue?", body_style))
    
    story.append(Paragraph("11.1 Customer Verification", h2_style))
    story.append(Paragraph("• Authenticate customer before exposing personal complaint information.", bullet_style))
    story.append(Paragraph("• For a new complaint, summarize extracted details and ask for confirmation before ticket creation.", bullet_style))
    story.append(Paragraph("• For an existing complaint, identify it through the authenticated customer's account rather than trusting an arbitrary ticket ID.", bullet_style))
    story.append(Paragraph("• If required information is missing or inconsistent, ask targeted clarification questions.", bullet_style))

    story.append(Paragraph("11.2 Ticket Status Visibility", h2_style))
    story.append(Paragraph("• Customer can ask for the status in natural language (English, Hindi, Hinglish).", bullet_style))
    story.append(Paragraph("• Assistant retrieves the current authoritative state directly from SQLite (tci.db).", bullet_style))
    story.append(Paragraph("• Response includes status, last update, assigned team, SLA countdown, and a short explanation.", bullet_style))
    story.append(Paragraph("• Status history is available for transparency in the customer drawer.", bullet_style))

    story.append(Paragraph("11.3 Resolution Confirmation", h2_style))
    story.append(Paragraph("• AI/admin proposes a resolution → Ticket enters RESOLVED_PENDING_CONFIRMATION.", bullet_style))
    story.append(Paragraph("• Customer is explicitly asked whether the issue is fixed.", bullet_style))
    story.append(Paragraph("• <b>YES</b> → record confirmation → CLOSED → CSAT feedback.", bullet_style))
    story.append(Paragraph("• <b>NO</b> → REOPENED / HUMAN_ESCALATION → support queue.", bullet_style))

    story.append(Paragraph("11.4 Customer Feedback", h2_style))
    story.append(Paragraph("After closure, the customer can provide a 1–5 star rating and optional comment. Feedback is stored against the complaint and surfaced in admin analytics for resolution-quality monitoring.", body_style))
    story.append(PageBreak())

    # ================= PAGE 13 =================
    story.append(Paragraph("12. Mass Complaint Intelligence & Root-Cause Analysis", h1_style))
    story.append(Paragraph("The operational intelligence features turn raw complaints into actionable network insights.", body_style))
    
    story.append(Paragraph("12.1 Complaint Spike Detection", h2_style))
    story.append(Paragraph("• Group complaints by time window (6h rolling), region, category and service type.", bullet_style))
    story.append(Paragraph("• Compare current volume against a rolling 7-day historical baseline.", bullet_style))
    story.append(Paragraph("• Flag statistically abnormal increases (3x to 300x surge) according to configured thresholds.", bullet_style))
    story.append(Paragraph("• Create or update an incident record and link future matching complaints.", bullet_style))

    story.append(Paragraph("12.2 Geographic Heatmap", h2_style))
    story.append(Paragraph("• Show complaint density by region via interactive Leaflet map.", bullet_style))
    story.append(Paragraph("• Filter by time, category, service and severity.", bullet_style))
    story.append(Paragraph("• Drill down from region → incident → complaint list.", bullet_style))
    story.append(Paragraph("• Highlight abnormal regions (Red surge circles) and active incidents.", bullet_style))

    story.append(Paragraph("12.3 AI Root-Cause Investigator", h2_style))
    rc_data = [
        [Paragraph("Evidence Signal", table_header_style), Paragraph("Analytical Computation", table_header_style), Paragraph("Example", table_header_style)],
        [Paragraph("Volume anomaly", table_cell_bold), Paragraph("Multiplier vs historical rolling baseline.", table_cell_style), Paragraph("Complaint count is 352x above baseline in Raj Nagar.", table_cell_style)],
        [Paragraph("Geographic concentration", table_cell_bold), Paragraph("Percentage of complaints in target area.", table_cell_style), Paragraph("94.2% of complaints are from Ghaziabad circle.", table_cell_style)],
        [Paragraph("Service concentration", table_cell_bold), Paragraph("Dominant service proportion.", table_cell_style), Paragraph("98.1% of complaints involve broadband/fiber.", table_cell_style)],
        [Paragraph("Time correlation", table_cell_bold), Paragraph("Temporal cluster window onset.", table_cell_style), Paragraph("Complaints started sharply within a 2-hour window.", table_cell_style)],
        [Paragraph("Historical similarity", table_cell_bold), Paragraph("Cosine similarity to past incidents.", table_cell_style), Paragraph("92% match to INC-2025-0873 (Optical fiber cut).", table_cell_style)],
        [Paragraph("Knowledge evidence", table_cell_bold), Paragraph("ChromaDB SOP corroboration.", table_cell_style), Paragraph("Retrieved SOP supports physical line severance.", table_cell_style)],
    ]
    story.append(make_table(rc_data, [100, 160, 244]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Root-cause output:</b> likely cause + confidence gauge (90%+) + evidence signals (>=3 checkable bullets) + affected scope + recommended action. AI output remains a hypothesis until confirmed by operations.", body_style))
    story.append(PageBreak())

    # ================= PAGE 14 =================
    story.append(Paragraph("13. Proactive Customer Notification", h1_style))
    notif_data = [
        [Paragraph("Trigger", table_header_style), Paragraph("Notification Content & Purpose", table_header_style)],
        [Paragraph("Ticket created", table_cell_bold), Paragraph("Complaint/ticket reference ID, summary and SLA deadline target.", table_cell_style)],
        [Paragraph("Ticket assigned", table_cell_bold), Paragraph("Support ownership update indicating assigned engineering department.", table_cell_style)],
        [Paragraph("Status changed", table_cell_bold), Paragraph("Meaningful lifecycle update with customer-visible admin note.", table_cell_style)],
        [Paragraph("Resolution proposed", table_cell_bold), Paragraph("Customer asked to verify service in chat before closure.", table_cell_style)],
        [Paragraph("Incident detected/confirmed", table_cell_bold), Paragraph("Affected customers in region informed of known issue and ETA.", table_cell_style)],
        [Paragraph("Complaint reopened", table_cell_bold), Paragraph("Customer and support receive relevant update on escalation.", table_cell_style)],
        [Paragraph("SLA risk/breach", table_cell_bold), Paragraph("Customer and support alerted where priority threshold is reached.", table_cell_style)],
    ]
    story.append(make_table(notif_data, [130, 374]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("13.1 MVP Notification Policy", h2_style))
    story.append(Paragraph(
        "In-app transactional updates are generated automatically from authenticated complaint state. "
        "<b>Mass proactive incident notifications must be reviewed and approved by an admin in the Notify Queue "
        "(<code>/admin/notifications</code>) to eliminate false-positive broadcast spam.</b> SMS/push provider integration is "
        "supported as optional webhooks.", body_style))
    story.append(PageBreak())

    # ================= PAGE 15 =================
    story.append(Paragraph("14. Dynamic Network & Line Diagnostics", h1_style))
    story.append(Paragraph("To deliver real-time utility beyond conversational text, the platform provides an on-demand network telemetry diagnostic tool (<code>/api/chat/diagnostic</code>).", body_style))
    
    diag_data = [
        [Paragraph("Metric", table_header_style), Paragraph("Broadband / Fiber", table_header_style), Paragraph("Mobile Data", table_header_style), Paragraph("Degraded (Active Outage)", table_header_style)],
        [Paragraph("Download Speed", table_cell_bold), Paragraph("94.0 - 298.0 Mbps", table_cell_style), Paragraph("35.0 - 78.0 Mbps", table_cell_style), Paragraph("1.5 - 12.0 Mbps", table_cell_style)],
        [Paragraph("Upload Speed", table_cell_bold), Paragraph("88.0 - 290.0 Mbps", table_cell_style), Paragraph("15.0 - 32.0 Mbps", table_cell_style), Paragraph("0.5 - 4.0 Mbps", table_cell_style)],
        [Paragraph("Ping Latency", table_cell_bold), Paragraph("12.0 - 28.0 ms", table_cell_style), Paragraph("22.0 - 45.0 ms", table_cell_style), Paragraph("120.0 - 280.0 ms", table_cell_style)],
        [Paragraph("Jitter", table_cell_bold), Paragraph("1.2 - 4.5 ms", table_cell_style), Paragraph("3.5 - 8.0 ms", table_cell_style), Paragraph("25.0 - 65.0 ms", table_cell_style)],
        [Paragraph("Packet Loss", table_cell_bold), Paragraph("0.0%", table_cell_style), Paragraph("0.0 - 0.5%", table_cell_style), Paragraph("8.0 - 22.0%", table_cell_style)],
        [Paragraph("Line Health", table_cell_bold), Paragraph("Optimal / Healthy", table_cell_style), Paragraph("Optimal / Healthy", table_cell_style), Paragraph("Degraded (Incident Linked)", table_cell_style)],
    ]
    story.append(make_table(diag_data, [100, 130, 120, 154]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Customer requests speed test → Backend inspects customer region & active incidents → Returns telemetry payload → Rendered as a visual diagnostic card in chat.", body_style))
    story.append(PageBreak())

    # ================= PAGE 16 =================
    story.append(Paragraph("15. Backend REST API Specifications", h1_style))
    api_data = [
        [Paragraph("Method & Route", table_header_style), Paragraph("Role", table_header_style), Paragraph("Purpose & Functionality", table_header_style)],
        [Paragraph("POST /api/auth/login", table_cell_bold), Paragraph("Public", table_cell_style), Paragraph("Customer/admin authentication using implemented password hashing and role-aware authorization.", table_cell_style)],
        [Paragraph("POST /api/auth/signup", table_cell_bold), Paragraph("Public", table_cell_style), Paragraph("Customer self-registration with region and service.", table_cell_style)],
        [Paragraph("POST /api/chat", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Text conversational endpoint executing LangGraph StateGraph.", table_cell_style)],
        [Paragraph("POST /api/chat/diagnostic", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Executes real-time network speed/latency diagnostics.", table_cell_style)],
        [Paragraph("GET /api/my/tickets", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Lists authenticated customer's own tickets.", table_cell_style)],
        [Paragraph("GET /api/my/tickets/{id}/history", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Status history timeline for a specific owned ticket.", table_cell_style)],
        [Paragraph("POST /api/admin/upload/ingest", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Universal CSV ingestion with auto-schema mapping & ETL.", table_cell_style)],
        [Paragraph("GET /api/admin/queue", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Filterable, paginated priority-ranked ticket queue.", table_cell_style)],
        [Paragraph("PATCH /api/admin/complaints/{id}", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Updates ticket status, team assignment, and notes.", table_cell_style)],
        [Paragraph("POST /api/admin/complaints/{id}/propose-resolution", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Proposes technical fix (resolved_pending_confirmation).", table_cell_style)],
        [Paragraph("GET /api/admin/heatmap", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Regional complaint density & spike data for Leaflet map.", table_cell_style)],
        [Paragraph("GET /api/admin/incidents", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Lists active outage incidents & root-cause dossiers.", table_cell_style)],
        [Paragraph("POST /api/admin/assistant/chat", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Admin AI Assistant decision support LangGraph endpoint.", table_cell_style)],
        [Paragraph("GET /api/admin/audit", table_cell_bold), Paragraph("Admin", table_cell_style), Paragraph("Immutable security & administrative audit logs.", table_cell_style)],
    ]
    story.append(make_table(api_data, [150, 70, 284]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("15.1 API Security", h2_style))
    story.append(Paragraph("• hashlib-based password hashing and role-aware authorization on protected routes.<br/>"
                           "• Customer ownership verification on every complaint read/write.<br/>"
                           "• Server-side validation of all status transitions.<br/>"
                           "• Comprehensive audit logging for privileged actions.<br/>"
                           "• API keys and secrets stored securely in environment variables.", body_style))
    story.append(PageBreak())

    # ================= PAGE 17 =================
    story.append(Paragraph("16. Free / Low-Cost AI & API Strategy", h1_style))
    story.append(Paragraph("The platform is engineered to run on 100% free-tier or open-source components with zero required software spend.", body_style))
    
    cost_data = [
        [Paragraph("Component", table_header_style), Paragraph("MVP Choice", table_header_style), Paragraph("Operational Role & Cost Profile", table_header_style)],
        [Paragraph("Generative LLM API", table_cell_bold), Paragraph("Groq Free Plan", table_cell_style), Paragraph("Assistant responses, ticket summaries, root-cause narratives (Zero cost).", table_cell_style)],
        [Paragraph("Embeddings", table_cell_bold), Paragraph("sentence-transformers", table_cell_style), Paragraph("all-MiniLM-L6-v2 local CPU embeddings (Zero cost).", table_cell_style)],
        [Paragraph("Vector Store", table_cell_bold), Paragraph("ChromaDB (local)", table_cell_style), Paragraph("Persistent vector store for SOP retrieval (Zero cost).", table_cell_style)],
        [Paragraph("Multilingual Tokenizer", table_cell_bold), Paragraph("Hugging Face DistilBERT", table_cell_style), Paragraph("distilbert-base-multilingual-cased (Zero cost).", table_cell_style)],
        [Paragraph("Classification & ML", table_cell_bold), Paragraph("scikit-learn", table_cell_style), Paragraph("Complaint category and intent classification (Zero cost).", table_cell_style)],
        [Paragraph("Database", table_cell_bold), Paragraph("SQLite (local)", table_cell_style), Paragraph("Live operational state in WAL mode (Zero cost).", table_cell_style)],
        [Paragraph("Backend", table_cell_bold), Paragraph("Python + FastAPI", table_cell_style), Paragraph("REST API and background scheduler (Zero cost).", table_cell_style)],
        [Paragraph("Geocoding", table_cell_bold), Paragraph("Geoapify (Free tier)", table_cell_style), Paragraph("Location coordinates with memory cache (Zero cost).", table_cell_style)],
    ]
    story.append(make_table(cost_data, [110, 130, 264]))
    story.append(PageBreak())

    # ================= PAGE 18 =================
    story.append(Paragraph("17. Non-Functional Requirements", h1_style))
    nfr_data = [
        [Paragraph("Category", table_header_style), Paragraph("Requirement & Implemented Standard", table_header_style)],
        [Paragraph("Performance", table_cell_bold), Paragraph("Customer/API interaction latency <= 1.5s on live Groq LLM, <= 50ms on offline fallback.", table_cell_style)],
        [Paragraph("Availability", table_cell_bold), Paragraph("Ticket/status operations remain usable even if external LLM services are offline.", table_cell_style)],
        [Paragraph("Security", table_cell_bold), Paragraph("hashlib-based password hashing and role-based authorization guards; no JWT requirement in the implemented flow.", table_cell_style)],
        [Paragraph("Privacy", table_cell_bold), Paragraph("Automatic regex PII redaction of names, phone numbers and emails upon ingestion.", table_cell_style)],
        [Paragraph("Reliability", table_cell_bold), Paragraph("Deterministic SQLite transactions; AI failures never create invalid states.", table_cell_style)],
        [Paragraph("Explainability", table_cell_bold), Paragraph("AI classification, priority scores and root causes expose contributing factors and evidence.", table_cell_style)],
        [Paragraph("Auditability", table_cell_bold), Paragraph("Status, assignment, resolution, escalation and notification actions are logged immutably.", table_cell_style)],
        [Paragraph("Language", table_cell_bold), Paragraph("English, Hindi (Devanagari) and Hinglish transliteration support.", table_cell_style)],
        [Paragraph("Cost", table_cell_bold), Paragraph("Free-tier architecture with zero cloud infrastructure overhead for the hackathon MVP.", table_cell_style)],
    ]
    story.append(make_table(nfr_data, [100, 404]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("17.1 AI Safety Rules", h2_style))
    story.append(Paragraph("• Never fabricate live ticket status or ticket IDs.<br/>"
                           "• Never claim an outage is confirmed when it is only an unverified AI hypothesis.<br/>"
                           "• Never claim resolution without explicit customer confirmation.<br/>"
                           "• Never reveal another customer's private data.<br/>"
                           "• Never perform privileged database actions directly from generated text.<br/>"
                           "• When confidence or evidence is insufficient, ask for clarification or escalate.", body_style))
    story.append(PageBreak())

    # ================= PAGE 19 =================
    story.append(Paragraph("18. Technology Stack — Implemented Project Stack", h1_style))
    tech_data = [
        [Paragraph("Area", table_header_style), Paragraph("Technology / Implementation", table_header_style)],
        [Paragraph("Admin Frontend", table_cell_bold), Paragraph("React + Vite; Admin Operations Dashboard; Admin AI Assistant; Recharts; React-Leaflet; shared Dark/Light Theme Engine.", table_cell_style)],
        [Paragraph("Customer Frontend", table_cell_bold), Paragraph("React + Vite; 40/60 customer text-chat layout; diagnostic cards.", table_cell_style)],
        [Paragraph("Backend", table_cell_bold), Paragraph("Python + FastAPI + Uvicorn; REST-style backend APIs and deterministic business logic.", table_cell_style)],
        [Paragraph("Authentication", table_cell_bold), Paragraph("hashlib-based password hashing with role-aware authorization.", table_cell_style)],
        [Paragraph("AI Orchestration", table_cell_bold), Paragraph("LangGraph Multi-Task StateGraph; separate customer and admin workflows.", table_cell_style)],
        [Paragraph("ML / NLP", table_cell_bold), Paragraph("Hugging Face DistilBERT multilingual model; scikit-learn TF-IDF + Logistic Regression; multi-factor priority scoring.", table_cell_style)],
        [Paragraph("RAG / Knowledge", table_cell_bold), Paragraph("ChromaDB persistent vector store + Sentence Transformers (all-MiniLM-L6-v2).", table_cell_style)],
        [Paragraph("Generative AI", table_cell_bold), Paragraph("Groq Cloud API for Llama models, with deterministic offline fallbacks.", table_cell_style)],
        [Paragraph("Database", table_cell_bold), Paragraph("SQLite 3 (tci.db) with WAL mode, foreign keys, status history and audit logs.", table_cell_style)],
        [Paragraph("Geolocation", table_cell_bold), Paragraph("Geoapify Geocoding REST API with caching; Leaflet for regional heatmaps.", table_cell_style)],
        [Paragraph("Development / Runtime", table_cell_bold), Paragraph("VS Code, npm/Vite frontend workflow, Python virtual environment, FastAPI/Uvicorn backend runtime.", table_cell_style)],
    ]
    story.append(make_table(tech_data, [120, 384]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("18.1 Separation of Responsibilities", h2_style))
    sep_data = [
        [Paragraph("System", table_header_style), Paragraph("Should Do", table_header_style), Paragraph("Should Not Do", table_header_style)],
        [Paragraph("SQLite", table_cell_bold), Paragraph("Store authoritative live operational state.", table_cell_style), Paragraph("Generate natural-language answers.", table_cell_style)],
        [Paragraph("ChromaDB", table_cell_bold), Paragraph("Retrieve semantic SOP knowledge.", table_cell_style), Paragraph("Store authoritative live ticket status.", table_cell_style)],
        [Paragraph("scikit-learn ML", table_cell_bold), Paragraph("Classify/score structured complaint data.", table_cell_style), Paragraph("Perform privileged database mutation.", table_cell_style)],
        [Paragraph("Groq LLM", table_cell_bold), Paragraph("Reason over supplied context and generate language.", table_cell_style), Paragraph("Invent current system state or ticket IDs.", table_cell_style)],
        [Paragraph("FastAPI", table_cell_bold), Paragraph("Authorize and execute state transitions.", table_cell_style), Paragraph("Depend on generated text for authorization.", table_cell_style)],
        [Paragraph("Admin Dashboard", table_cell_bold), Paragraph("Operate, monitor and approve broadcasts.", table_cell_style), Paragraph("Bypass backend authorization or audit logs.", table_cell_style)],
    ]
    story.append(make_table(sep_data, [95, 195, 214]))
    story.append(PageBreak())

    # ================= PAGE 20 =================
    story.append(Paragraph("19. Testing & Acceptance Criteria", h1_style))
    test_scenarios = [
        [Paragraph("Scenario", table_header_style), Paragraph("Admin-Oriented Acceptance Criteria", table_header_style)],
        [Paragraph("Admin overview", table_cell_bold), Paragraph("Dashboard shows complaint volume, open/resolved tickets, high priority, SLA risk and active incidents.", table_cell_style)],
        [Paragraph("Queue management", table_cell_bold), Paragraph("Admin can search/filter, assign, update, escalate and inspect ticket history.", table_cell_style)],
        [Paragraph("Incident investigation", table_cell_bold), Paragraph("Spike detection creates/updates an incident and links matching complaints.", table_cell_style)],
        [Paragraph("Root cause", table_cell_bold), Paragraph("Dashboard shows evidence signals, confidence and affected scope for an AI hypothesis.", table_cell_style)],
        [Paragraph("Admin AI", table_cell_bold), Paragraph("Operations AI answers using live DB snapshots and approved ChromaDB SOPs without unrestricted DB access.", table_cell_style)],
        [Paragraph("Notification approval", table_cell_bold), Paragraph("Admin reviews/approves proactive incident notifications before broadcast.", table_cell_style)],
        [Paragraph("Customer resolution", table_cell_bold), Paragraph("Customer confirmation closes an eligible complaint; rejection reopens/escalates.", table_cell_style)],
        [Paragraph("Authorization", table_cell_bold), Paragraph("A customer cannot read another customer's complaint even with its ticket ID.", table_cell_style)],
        [Paragraph("AI outage", table_cell_bold), Paragraph("Groq unavailable → deterministic ticket/status APIs continue to work with offline fallbacks.", table_cell_style)],
    ]
    story.append(make_table(test_scenarios, [120, 384]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("19.1 Key KPIs & Validated Benchmarks", h2_style))
    story.append(Paragraph("• <b>Complaint classification macro-F1:</b> >= 82.4% on the held-out split.<br/>"
                           "• <b>Intent routing accuracy:</b> >= 95.0% across 15+ supported intents.<br/>"
                           "• <b>Ticket creation correctness:</b> 100% in automated workflow tests.<br/>"
                           "• <b>Status retrieval correctness:</b> 100% in authorized customer tests.<br/>"
                           "• <b>Resolution confirmation capture:</b> 100% of AI-assisted resolution attempts.<br/>"
                           "• <b>Test suite pass rate:</b> 100% (106+ passing backend tests as specified in the PRD).", body_style))
    story.append(PageBreak())

    # ================= PAGE 21 =================
    story.append(Paragraph("20. Implementation Plan & Demo", h1_style))
    plan_phases = [
        [Paragraph("Phase", table_header_style), Paragraph("Implementation Milestone", table_header_style)],
        [Paragraph("1", table_cell_bold), Paragraph("Admin dashboard foundation, SQLite schema, authentication, role-based access and demo accounts.", table_cell_style)],
        [Paragraph("2", table_cell_bold), Paragraph("FastAPI complaint/status APIs, CSV schema mapper and audit logging.", table_cell_style)],
        [Paragraph("3", table_cell_bold), Paragraph("Admin AI Assistant + LangGraph admin workflow + live DB snapshots + ChromaDB SOP retrieval.", table_cell_style)],
        [Paragraph("4", table_cell_bold), Paragraph("Admin queue, ticket drawer, assignment, priority/SLA and status management.", table_cell_style)],
        [Paragraph("5", table_cell_bold), Paragraph("Leaflet heatmap, Geoapify geocoding, spike detection and incident management.", table_cell_style)],
        [Paragraph("6", table_cell_bold), Paragraph("Root-cause investigator, evidence dossier and confidence gauge.", table_cell_style)],
        [Paragraph("7", table_cell_bold), Paragraph("Proactive notification queue, admin approval and in-app notification feed.", table_cell_style)],
        [Paragraph("8", table_cell_bold), Paragraph("Customer LangGraph assistant, conversation state, intent routing and DistilBERT.", table_cell_style)],
        [Paragraph("9", table_cell_bold), Paragraph("Complaint verification, ticket creation, live status tracking and line diagnostics.", table_cell_style)],
        [Paragraph("10", table_cell_bold), Paragraph("ChromaDB/SentenceTransformers troubleshooting and resolution confirmation loop.", table_cell_style)],
        [Paragraph("11", table_cell_bold), Paragraph("Reopen/escalation workflow, customer feedback and analytics.", table_cell_style)],
        [Paragraph("12", table_cell_bold), Paragraph("Theme engine (Dark/Light), text-chat UI validation and full test-suite validation.", table_cell_style)],
    ]
    story.append(make_table(plan_phases, [45, 459]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("20.1 Minimum Successful Admin Demo", h2_style))
    story.append(Paragraph("• Admin opens the dashboard and immediately sees queue, priority, SLA, incident and trend information.<br/>"
                           "• Admin filters a complaint cluster and investigates the associated incident/heatmap.<br/>"
                           "• Admin asks the Operations AI Assistant why the spike is occurring and receives evidence-backed analysis.<br/>"
                           "• Admin assigns the affected tickets to the appropriate support/network team.<br/>"
                           "• Admin updates status and proposes a resolution; the customer receives the update.<br/>"
                           "• Customer confirms or rejects the resolution; the dashboard reflects the resulting closed or reopened state.<br/>"
                           "• Admin reviews and approves a proactive notification for affected customers.<br/>"
                           "• Admin uses the audit trail to verify the operational actions.", body_style))
    story.append(PageBreak())

    # ================= PAGE 22 =================
    story.append(Paragraph("21. Product Differentiation", h1_style))
    diff_data = [
        [Paragraph("Traditional Complaint System", table_header_style), Paragraph("Proposed TelConnect Platform", table_header_style)],
        [Paragraph("Passive ticketing", table_cell_bold), Paragraph("Admin control plane with live queue, assignments, SLA and resolution actions.", table_cell_style)],
        [Paragraph("Fragmented reporting", table_cell_bold), Paragraph("Unified operational intelligence across complaints, incidents, heatmaps and analytics.", table_cell_style)],
        [Paragraph("Manual investigation", table_cell_bold), Paragraph("Admin AI Assistant combines live DB context, SOP retrieval and evidence synthesis.", table_cell_style)],
        [Paragraph("Outages discovered late", table_cell_bold), Paragraph("Complaint spikes trigger anomaly alerts, incident records and root-cause dossiers.", table_cell_style)],
        [Paragraph("No governance layer", table_cell_bold), Paragraph("Role-based access, controlled actions, immutable audit logs and notification approval.", table_cell_style)],
        [Paragraph("Customer status is opaque", table_cell_bold), Paragraph("Admin updates flow to the customer text channel with live authoritative state.", table_cell_style)],
        [Paragraph("Dataset-driven operation", table_cell_bold), Paragraph("SQLite is the dynamic operational source; CSV is seed/analysis data only.", table_cell_style)],
        [Paragraph("Generic AI chatbot", table_cell_bold), Paragraph("Controlled LangGraph multi-task agents connected to authorized backend functions.", table_cell_style)],
    ]
    story.append(make_table(diff_data, [230, 274]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("21.1 Final Product Definition", h2_style))
    story.append(Paragraph(
        "<b>An admin-oriented telecom complaint intelligence and automated resolution platform that gives support and network operations "
        "teams a unified control plane for complaint triage, ticket management, incident detection, heatmaps, root-cause analysis, AI decision "
        "support, proactive notifications and auditability, while a connected customer text assistant provides diagnostics, troubleshooting, status "
        "tracking and explicit resolution confirmation.</b>", body_style))
    story.append(PageBreak())

    # ================= PAGE 23 =================
    story.append(Paragraph("22. Recommended Presentation Flow", h1_style))
    pres_data = [
        [Paragraph("Scene", table_header_style), Paragraph("Admin-Led Demonstration", table_header_style), Paragraph("Message to Judges", table_header_style)],
        [Paragraph("Admin overview", table_cell_bold), Paragraph("Open dashboard with queue, SLA risk, incidents and trends.", table_cell_style), Paragraph("TelConnect starts with operational visibility.", table_cell_style)],
        [Paragraph("Complaint intelligence", table_cell_bold), Paragraph("Open a complaint and show category, sentiment, urgency, priority and escalation risk.", table_cell_style), Paragraph("The system turns raw complaints into actionable intelligence.", table_cell_style)],
        [Paragraph("Incident / heatmap", table_cell_bold), Paragraph("Inspect a spike and drill into region, service and affected complaints.", table_cell_style), Paragraph("Operations can detect service-wide issues early.", table_cell_style)],
        [Paragraph("Admin AI Assistant", table_cell_bold), Paragraph("Ask why the spike is occurring and retrieve SOP/evidence.", table_cell_style), Paragraph("AI supports decisions without bypassing authorization.", table_cell_style)],
        [Paragraph("Ticket action", table_cell_bold), Paragraph("Assign, update, escalate or propose resolution from the dashboard.", table_cell_style), Paragraph("The admin remains in control of operational actions.", table_cell_style)],
        [Paragraph("Customer confirmation", table_cell_bold), Paragraph("Customer accepts/rejects the fix; dashboard reflects the outcome.", table_cell_style), Paragraph("Closed-loop resolution prevents silent closure.", table_cell_style)],
        [Paragraph("Notification", table_cell_bold), Paragraph("Admin reviews and approves a proactive incident notification.", table_cell_style), Paragraph("Human-in-the-loop reduces false-positive broadcasts.", table_cell_style)],
        [Paragraph("Audit", table_cell_bold), Paragraph("Show status/action history.", table_cell_style), Paragraph("Every privileged action is traceable.", table_cell_style)],
        [Paragraph("Customer channel", table_cell_bold), Paragraph("Briefly demonstrate text chat, diagnostics and live status.", table_cell_style), Paragraph("The customer experience is the service channel, not the operational control plane.", table_cell_style)],
    ]
    story.append(make_table(pres_data, [95, 205, 204]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("23. Requirements Traceability to Use Case 13", h1_style))
    req_map = [
        [Paragraph("Use Case Requirement", table_header_style), Paragraph("PRD Implementation", table_header_style)],
        [Paragraph("Prioritize critical complaints", table_cell_bold), Paragraph("Multi-Factor Priority Scoring + Admin Queue + SLA deadlines.", table_cell_style)],
        [Paragraph("Predict escalation risk", table_cell_bold), Paragraph("Escalation Risk model + alerts.", table_cell_style)],
        [Paragraph("Detect service problems", table_cell_bold), Paragraph("Spike detection + Leaflet heatmap + Incident Management.", table_cell_style)],
        [Paragraph("Recommend resolution actions", table_cell_bold), Paragraph("ChromaDB Vector RAG + approved SOP procedures.", table_cell_style)],
        [Paragraph("Complaint triage assistant", table_cell_bold), Paragraph("LangGraph customer multi-task workflow.", table_cell_style)],
        [Paragraph("Operations AI decision support", table_cell_bold), Paragraph("LangGraph Admin Operations Agent (/admin/assistant).", table_cell_style)],
        [Paragraph("Classify complaint categories", table_cell_bold), Paragraph("TF-IDF + Logistic Regression (Macro-F1 >= 82.4%).", table_cell_style)],
        [Paragraph("Customer experience", table_cell_bold), Paragraph("40/60 text chat, line diagnostics, confirm-to-close loop.", table_cell_style)],
    ]
    story.append(make_table(req_map, [150, 354]))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_path}")


if __name__ == "__main__":
    build_new_prd_pdf(NEW_PRD_PDF_DOCS)
    build_new_prd_pdf(NEW_PRD_PDF_ROOT)
