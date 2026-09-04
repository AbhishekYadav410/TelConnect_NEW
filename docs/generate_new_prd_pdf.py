"""Generate NEW_PRD.pdf matching the professional 23-page template structure and styling."""
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
        self.drawString(54, 32, "PRD v7.0 — Autonomous Multi-Task Agent & Multilingual Intelligence")
        self.drawRightString(558, 32, f"PRD v7.0 | Page {self._pageNumber} of {page_count}")
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
    story.append(Paragraph("Professional, customer-first product specification<br/><b>Cognizant Hackathon • Use Case 13</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=8))

    spec_data = [
        [Paragraph("Document", table_header_style), Paragraph("Specification", table_header_style)],
        [Paragraph("Version", table_cell_bold), Paragraph("7.0 — Autonomous Multi-Task Agent & Multilingual Intelligence PRD", table_cell_style)],
        [Paragraph("Product Type", table_cell_bold), Paragraph("AI-powered telecom complaint intelligence and automated resolution platform", table_cell_style)],
        [Paragraph("Primary User", table_cell_bold), Paragraph("Telecom customer", table_cell_style)],
        [Paragraph("Operational User", table_cell_bold), Paragraph("Support / Network / Operations / Admin teams", table_cell_style)],
        [Paragraph("Agent Orchestration", table_cell_bold), Paragraph("LangGraph Multi-Task StateGraph (6-node customer agent & 4-node admin agent)", table_cell_style)],
        [Paragraph("Multilingual Engine", table_cell_bold), Paragraph("Hugging Face DistilBERT (multilingual-cased) + Groq Zero-Shot Neural Translation + Rule Fallback", table_cell_style)],
        [Paragraph("Primary AI Provider", table_cell_bold), Paragraph("Groq API — Free Plan (Llama-3 models + Whisper voice STT) with complete offline fallback", table_cell_style)],
        [Paragraph("Voice Stack", table_cell_bold), Paragraph("Groq Whisper (Multilingual Voice STT) + Browser Web Speech API (Bilingual TTS Readout)", table_cell_style)],
        [Paragraph("Core Data Store", table_cell_bold), Paragraph("SQLite (tci.db with WAL mode, foreign keys, and immutable audit logs)", table_cell_style)],
        [Paragraph("Knowledge Store", table_cell_bold), Paragraph("ChromaDB persistent vector store + Sentence Transformers (all-MiniLM-L6-v2)", table_cell_style)],
        [Paragraph("Geolocation Engine", table_cell_bold), Paragraph("Geoapify Geocoding API (in-memory caching and India coordinate boundary validation)", table_cell_style)],
        [Paragraph("Core Backend", table_cell_bold), Paragraph("Python + FastAPI + Uvicorn", table_cell_style)],
        [Paragraph("UI", table_cell_bold), Paragraph("Customer Assistant (40/60 Split) + Admin Operations Dashboard + Theme Engine (Dark/Light)", table_cell_style)],
    ]
    story.append(make_table(spec_data, [110, 394], header_color=primary_color))
    story.append(Spacer(1, 8))

    vision_text = (
        "<b>Product vision:</b> Turn telecom complaints from isolated support tickets into a closed-loop "
        "intelligence system that can understand the customer in any language, verify the issue with live line diagnostics, "
        "resolve eligible problems using grounded SOPs, track unresolved cases transparently, detect mass incidents in real time, "
        "and proactively prevent repeated complaints."
    )
    t_callout = Table([[Paragraph(vision_text, callout_style)]], colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdfa")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0d9488")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This PRD preserves and elevates all capabilities from the original Use Case 13 — complaint classification, "
        "sentiment, escalation prediction, RAG, root-cause analysis, heatmaps, spike detection and proactive notification — "
        "while structuring them around the customer's complaint-to-resolution journey and modern multi-task agent workflows.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("1. Product Overview", h1_style))
    story.append(Paragraph(
        "The Telecom Complaint Intelligence & Automated Resolution Assistant is a customer-facing AI service backed by an "
        "operational support and analytics platform. It accepts complaints through a conversational assistant via text or voice, "
        "classifies and prioritizes them, checks for known incidents, retrieves approved troubleshooting guidance, creates and "
        "tracks tickets when required, and verifies whether the customer is actually satisfied with the resolution.", body_style))
    story.append(Paragraph(
        "The Admin Dashboard is the operations control plane used to manage the complaint lifecycle, investigate patterns, "
        "monitor service issues, update ticket states, manage incidents, evaluate AI recommendations, and query operational intelligence.", body_style))
    
    story.append(Paragraph("1.1 Product Principles", h2_style))
    story.append(Paragraph("• <b>Customer first:</b> The primary workflow begins with the customer's problem and ends only when the issue is resolved or properly escalated.", bullet_style))
    story.append(Paragraph("• <b>One source of truth:</b> Customer assistant and admin dashboard read/write through the same backend and SQLite database (<code>tci.db</code>).", bullet_style))
    story.append(Paragraph("• <b>AI with controlled actions:</b> The LLM interprets and explains; backend APIs perform privileged operations.", bullet_style))
    story.append(Paragraph("• <b>Dynamic by design:</b> Complaints can be created by customers, admins or authorized data feeds; the system is not dependent on static CSV data.", bullet_style))
    story.append(Paragraph("• <b>Closed loop:</b> A proposed resolution requires customer confirmation before an eligible complaint is closed.", bullet_style))
    story.append(Paragraph("• <b>Explainable intelligence:</b> Classification, priority, escalation and root-cause outputs expose useful evidence and contributing factors.", bullet_style))
    story.append(Paragraph("• <b>Zero-Cost & Offline Resilient:</b> Runs 100% on free-tier APIs with immediate deterministic offline fallbacks for zero API key operation.", bullet_style))

    story.append(Paragraph("1.2 Problem Statement", h2_style))
    story.append(Paragraph(
        "Telecom operators receive large volumes of complaints related to network issues, call drops, broadband failures, "
        "billing disputes and service requests. Manual triage is slow, customers often lack visibility into what happens after raising "
        "a complaint, and support teams may discover mass outages only after complaint volumes increase.", body_style))
    story.append(Paragraph(
        "The product must therefore solve two connected problems: <b>(1) help individual customers reach a verified "
        "resolution faster</b>, and <b>(2) convert complaint data into operational intelligence</b> that helps telecom teams detect, "
        "investigate and prevent recurring or mass complaints.", body_style))
    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("2. Objectives", h1_style))
    obj_data = [
        [Paragraph("Objective", table_header_style), Paragraph("Expected Outcome", table_header_style)],
        [Paragraph("Automate complaint understanding", table_cell_bold), Paragraph("Classify intent/category, extract key entities, detect sentiment, urgency and escalation risk.", table_cell_style)],
        [Paragraph("Instant line & speed diagnostics", table_cell_bold), Paragraph("Provide on-demand telemetry tests (speed, latency, jitter, packet loss) directly inside chat.", table_cell_style)],
        [Paragraph("Improve first-contact resolution", table_cell_bold), Paragraph("Use incident checks, ChromaDB RAG and safe troubleshooting workflows before escalating to human support.", table_cell_style)],
        [Paragraph("Create a complete complaint lifecycle", table_cell_bold), Paragraph("Support verification, ticket creation, assignment, status updates, resolution, confirmation, reopening and escalation.", table_cell_style)],
        [Paragraph("Give customers live visibility", table_cell_bold), Paragraph("Allow authenticated customers to check ticket status and status history from the assistant in natural language.", table_cell_style)],
        [Paragraph("Reduce duplicate complaints", table_cell_bold), Paragraph("Match new complaints against active incidents and link reports without creating duplicate tickets.", table_cell_style)],
        [Paragraph("Detect mass service problems", table_cell_bold), Paragraph("Use complaint spikes, location and service patterns against rolling baselines to create incident alerts.", table_cell_style)],
        [Paragraph("Support root-cause investigation", table_cell_bold), Paragraph("Combine structured complaint patterns with historical/knowledge evidence to generate explainable hypotheses.", table_cell_style)],
        [Paragraph("Proactively inform customers", table_cell_bold), Paragraph("Notify affected customers about confirmed/approved incidents and meaningful ticket events.", table_cell_style)],
        [Paragraph("Operations AI decision support", table_cell_bold), Paragraph("Provide an autonomous LangGraph agent for NOC admins to query critical issues and SOPs.", table_cell_style)],
        [Paragraph("Improve operational efficiency", table_cell_bold), Paragraph("Provide an admin dashboard for queue management, heatmap investigation, analytics and resolution actions.", table_cell_style)],
    ]
    story.append(make_table(obj_data, [130, 374]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.1 Success Criteria", h2_style))
    story.append(Paragraph("• Customer can report a complaint or run speed diagnostics without navigating complex forms.", bullet_style))
    story.append(Paragraph("• Every valid complaint receives a unique ticket ID (<code>TCK-xxx</code>) and persistent database record.", bullet_style))
    story.append(Paragraph("• Customer can retrieve the current ticket status at any time in English, Hindi, or Hinglish.", bullet_style))
    story.append(Paragraph("• AI-assisted resolution never silently closes a complaint.", bullet_style))
    story.append(Paragraph("• A customer can reject a resolution and reopen/escalate the complaint.", bullet_style))
    story.append(Paragraph("• Admin status changes are reflected in the customer experience in real time.", bullet_style))
    story.append(Paragraph("• Known active incidents can be linked to new complaints to reduce duplicate tickets.", bullet_style))
    story.append(Paragraph("• Admin can see complaint volume, priority, category, sentiment, escalation risk, geographic spikes and incident information.", bullet_style))

    story.append(Paragraph("2.2 Scope Boundaries", h2_style))
    story.append(Paragraph("• MVP focuses on complaint intelligence and resolution orchestration; it does not directly control telecom network equipment.", bullet_style))
    story.append(Paragraph("• Real OSS/BSS integration is a future integration point; the hackathon uses simulated telemetry APIs and controlled data feeds.", bullet_style))
    story.append(Paragraph("• External SMS/push delivery is optional for MVP; in-app notifications are sufficient to demonstrate the workflow.", bullet_style))
    story.append(Paragraph("• The platform uses the supplied complaint dataset as seed data but does not treat the CSV as the live operational database.", bullet_style))
    story.append(PageBreak())

    # ================= PAGE 4 =================
    story.append(Paragraph("3. Users & Roles", h1_style))
    roles_data = [
        [Paragraph("Role", table_header_style), Paragraph("Needs", table_header_style), Paragraph("Key Capabilities", table_header_style)],
        [Paragraph("Customer", table_cell_bold), Paragraph("Fast help, line speed test, clear status, proof that complaint was resolved.", table_cell_style), Paragraph("Chat assistant, voice STT/TTS, line diagnostics, ticket creation, troubleshooting, ticket tracking, confirmation, reopen, escalation, notifications.", table_cell_style)],
        [Paragraph("Support Admin", table_cell_bold), Paragraph("Efficient queue and resolution management.", table_cell_style), Paragraph("Ticket queue, assignment, priority, status updates, notes, resolution actions, SLA monitoring, escalation.", table_cell_style)],
        [Paragraph("Network Operations", table_cell_bold), Paragraph("Detect and investigate service-wide problems.", table_cell_style), Paragraph("Leaflet heatmap, complaint spikes, incident management, root-cause investigation, affected-customer analysis, broadcast approvals.", table_cell_style)],
        [Paragraph("Operations AI User", table_cell_bold), Paragraph("Instant decision support and NOC briefings.", table_cell_style), Paragraph("Admin AI Assistant, prompt chips, live database snapshots, ChromaDB SOP synthesis, classification explanations.", table_cell_style)],
        [Paragraph("System / AI", table_cell_bold), Paragraph("Automate classification, scoring and decision support.", table_cell_style), Paragraph("LangGraph multi-task agents, ML scoring, spike detection, RAG retrieval, response generation, audit logging.", table_cell_style)],
    ]
    story.append(make_table(roles_data, [90, 140, 274]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3.1 Access Control", h2_style))
    story.append(Paragraph("• Customers can access only their own profile, conversations, complaints, notifications and feedback.", bullet_style))
    story.append(Paragraph("• Admins can access operational complaint and incident data according to role.", bullet_style))
    story.append(Paragraph("• AI services do not receive unrestricted database access; they call authorized backend functions.", bullet_style))
    story.append(Paragraph("• All privileged actions are recorded in an audit log.", bullet_style))
    story.append(PageBreak())

    # ================= PAGE 5 =================
    story.append(Paragraph("4. Customer Journey", h1_style))
    story.append(Paragraph("The customer journey is the central workflow of the product.", body_style))
    journey_data = [
        [Paragraph("Step", table_header_style), Paragraph("Customer Experience", table_header_style), Paragraph("System Behaviour", table_header_style)],
        [Paragraph("1. Start", table_cell_bold), Paragraph("Customer describes issue naturally or runs speed test.", table_cell_style), Paragraph("DistilBERT normalizes text; intent router identifies query type.", table_cell_style)],
        [Paragraph("2. Verify", table_cell_bold), Paragraph("Customer confirms service/account/issue details.", table_cell_style), Paragraph("Authentication + required field validation.", table_cell_style)],
        [Paragraph("3. Diagnose", table_cell_bold), Paragraph("Assistant checks known incident and retrieves relevant guidance.", table_cell_style), Paragraph("Incident engine + ChromaDB RAG + resolution rules + line diagnostic.", table_cell_style)],
        [Paragraph("4. Resolve", table_cell_bold), Paragraph("Customer follows safe troubleshooting steps if eligible.", table_cell_style), Paragraph("Resolution attempt recorded.", table_cell_style)],
        [Paragraph("5. Confirm", table_cell_bold), Paragraph("Customer says whether service is working.", table_cell_style), Paragraph("Confirmation stored as resolution outcome.", table_cell_style)],
        [Paragraph("6. Ticket", table_cell_bold), Paragraph("If unresolved, system creates/updates ticket.", table_cell_style), Paragraph("Ticket ID, priority (P1-P4), SLA and category persisted in SQLite.", table_cell_style)],
        [Paragraph("7. Track", table_cell_bold), Paragraph("Customer asks 'What is the status?'", table_cell_style), Paragraph("Current SQLite status + assigned team + history returned.", table_cell_style)],
        [Paragraph("8. Escalate", table_cell_bold), Paragraph("Customer requests human help or AI cannot safely resolve.", table_cell_style), Paragraph("Ticket routed to support queue with priority escalation.", table_cell_style)],
        [Paragraph("9. Reopen", table_cell_bold), Paragraph("Customer says issue returned/not fixed.", table_cell_style), Paragraph("Complaint reopened with previous resolution preserved.", table_cell_style)],
        [Paragraph("10. Close", table_cell_bold), Paragraph("Customer confirms final resolution.", table_cell_style), Paragraph("Complaint moves to CLOSED and 1-5 star CSAT feedback captured.", table_cell_style)],
    ]
    story.append(make_table(journey_data, [60, 194, 250]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Complaint Status Model", h2_style))
    story.append(Paragraph("<code>NEW</code> &rarr; <code>VERIFICATION_REQUIRED</code> &rarr; <code>VERIFIED</code> &rarr; <code>CLASSIFIED</code> &rarr; <code>DIAGNOSING</code> &rarr; <code>IN_PROGRESS</code> &rarr; <code>RESOLVED_PENDING_CONFIRMATION</code> &rarr; <code>CLOSED</code>", body_style))
    story.append(Paragraph("Alternative paths: <code>WAITING_FOR_CUSTOMER</code>, <code>HUMAN_ESCALATION</code>, <code>REOPENED</code>. Every status transition creates an immutable status-history record in SQLite with actor, timestamp and reason.", body_style))
    story.append(PageBreak())

    # ================= PAGE 6 =================
    story.append(Paragraph("5. AI Customer Assistant", h1_style))
    story.append(Paragraph(
        "The assistant behaves as a workflow-driven support agent, not as a generic chatbot. It identifies the customer's "
        "intent, collects missing information, calls the correct backend function, retrieves relevant knowledge from ChromaDB, "
        "and generates a grounded response.", body_style))
    
    story.append(Paragraph("5.1 Supported Intents", h2_style))
    intents_data = [
        [Paragraph("Intent", table_header_style), Paragraph("Action", table_header_style)],
        [Paragraph("REPORT_COMPLAINT", table_cell_bold), Paragraph("Collect details &rarr; verify &rarr; classify &rarr; create complaint.", table_cell_style)],
        [Paragraph("DIAGNOSTIC", table_cell_bold), Paragraph("Run dynamic network line diagnostic & render speed telemetry card.", table_cell_style)],
        [Paragraph("CHECK_STATUS", table_cell_bold), Paragraph("Retrieve authenticated customer's current ticket status/history.", table_cell_style)],
        [Paragraph("TROUBLESHOOT", table_cell_bold), Paragraph("Retrieve relevant approved SOP from ChromaDB and guide the customer.", table_cell_style)],
        [Paragraph("KNOWN_INCIDENT", table_cell_bold), Paragraph("Check active incident and explain known service impact.", table_cell_style)],
        [Paragraph("CONFIRM_RESOLUTION", table_cell_bold), Paragraph("Record customer confirmation and close eligible ticket.", table_cell_style)],
        [Paragraph("REJECT_RESOLUTION", table_cell_bold), Paragraph("Move complaint to REOPENED / escalation workflow.", table_cell_style)],
        [Paragraph("REOPEN_COMPLAINT", table_cell_bold), Paragraph("Reopen eligible complaint and preserve history.", table_cell_style)],
        [Paragraph("BILLING_QUERY", table_cell_bold), Paragraph("Provide approved billing guidance or route to support.", table_cell_style)],
        [Paragraph("ESCALATE", table_cell_bold), Paragraph("Create human-support escalation with priority adjustment.", table_cell_style)],
        [Paragraph("GENERAL_QUERY", table_cell_bold), Paragraph("Answer from approved knowledge or ask clarification.", table_cell_style)],
    ]
    story.append(make_table(intents_data, [130, 374]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.2 Assistant Architecture (LangGraph 6-Node Workflow)", h2_style))
    story.append(Paragraph("Customer message &rarr; <b>1. translate_input</b> (DistilBERT) &rarr; <b>2. route_intent</b> (Intent Classifier) &rarr; <b>3. retrieve_context</b> (ChromaDB RAG + Incidents) &rarr; <b>4. execute_action</b> (Speed Test / DB Mutations) &rarr; <b>5. synthesize_response</b> (Grounded Groq LLM) &rarr; <b>6. translate_output</b> (Devanagari Script & Cards).", body_style))

    story.append(Paragraph("5.3 Important Design Rule", h2_style))
    story.append(Paragraph(
        "<b>The LLM does not directly change ticket status or invent live data.</b> It can interpret the request and generate "
        "language, but actions such as creating a complaint, checking status, changing status, confirming resolution and "
        "reopening a complaint are performed through authenticated backend APIs.", body_style))
    story.append(PageBreak())

    # ================= PAGE 7 =================
    story.append(Paragraph("6. Solution Architecture", h1_style))
    arch_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Components", table_header_style), Paragraph("Purpose", table_header_style)],
        [Paragraph("Customer Layer", table_cell_bold), Paragraph("React 40/60 chat, voice STT/TTS, diagnostic cards", table_cell_style), Paragraph("Complaint reporting, speed diagnostics, troubleshooting, tracking and confirmation.", table_cell_style)],
        [Paragraph("Admin Layer", table_cell_bold), Paragraph("React operations dashboard, AI Assistant, Theme Engine", table_cell_style), Paragraph("Queue, ticket management, incidents, heatmap, analytics, alert inbox, notify queue, audit.", table_cell_style)],
        [Paragraph("API Layer", table_cell_bold), Paragraph("FastAPI + JWT authentication + scheduler", table_cell_style), Paragraph("Central business logic, authorization and deterministic actions.", table_cell_style)],
        [Paragraph("AI Orchestration", table_cell_bold), Paragraph("LangGraph Multi-Task StateGraph", table_cell_style), Paragraph("Controls multi-turn state continuation and tool execution.", table_cell_style)],
        [Paragraph("Multilingual NLP", table_cell_bold), Paragraph("Hugging Face DistilBERT (multilingual-cased)", table_cell_style), Paragraph("Tokenization, Hinglish normalization, Devanagari validation.", table_cell_style)],
        [Paragraph("ML Intelligence", table_cell_bold), Paragraph("scikit-learn (TF-IDF + LogReg), Multi-Factor Scoring", table_cell_style), Paragraph("Classification (Macro-F1 >= 82.4%), sentiment, urgency, escalation, priority scoring.", table_cell_style)],
        [Paragraph("Vector RAG", table_cell_bold), Paragraph("ChromaDB + Sentence Transformers (all-MiniLM-L6-v2)", table_cell_style), Paragraph("Grounded troubleshooting, FAQs, SOPs and approved resolved cases.", table_cell_style)],
        [Paragraph("Generative AI", table_cell_bold), Paragraph("Groq API (Llama-3, Whisper) + Offline Fallbacks", table_cell_style), Paragraph("Conversation generation, summaries, explanations and root-cause narrative.", table_cell_style)],
        [Paragraph("Geolocation", table_cell_bold), Paragraph("Geoapify Geocoding API + dynamic cache", table_cell_style), Paragraph("Location coordinates for Leaflet regional heatmap.", table_cell_style)],
        [Paragraph("Operational DB", table_cell_bold), Paragraph("SQLite (tci.db with WAL mode)", table_cell_style), Paragraph("Live complaints, users, status history, incidents, notifications and audit logs.", table_cell_style)],
        [Paragraph("Analytics / Detection", table_cell_bold), Paragraph("Spike detection, heatmap, incident engine", table_cell_style), Paragraph("Proactive service intelligence.", table_cell_style)],
    ]
    story.append(make_table(arch_data, [95, 175, 234]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.1 Data Flow", h2_style))
    story.append(Paragraph(
        "Customer/Admin/API input &rarr; validation &rarr; complaint persistence &rarr; SQLite &rarr; incident/duplicate evaluation &rarr; "
        "resolution/ChromaDB RAG &rarr; ticket lifecycle &rarr; notification/analytics &rarr; feedback.", body_style))
    story.append(Paragraph(
        "<b>SQLite is the operational source of truth. ChromaDB is the knowledge retrieval layer. Groq is the "
        "generation/reasoning service.</b> This separation prevents the chatbot from becoming the database or the source of "
        "live ticket truth.", body_style))
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
        "<b>Every troubleshooting response should be generated from retrieved approved knowledge.</b> The assistant should "
        "not claim a cause, ETA, policy or fix that is not supported by the retrieved ChromaDB chunks or live SQLite backend state.", body_style))
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
    story.append(Paragraph("10.2 Required Complaint Fields: <code>complaint_id, customer_id, text, category, region, lat, long, service_type, sentiment, urgency, escalation_risk, priority_score, priority_label, sla_deadline, status, incident_id, assigned_to, ticket_summary, created_at</code>", body_style))
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
    story.append(Paragraph("• Assistant retrieves the current authoritative state directly from SQLite (<code>tci.db</code>).", bullet_style))
    story.append(Paragraph("• Response includes status, last update, assigned team, SLA countdown, and a short explanation.", bullet_style))
    story.append(Paragraph("• Status history is available for transparency in the customer drawer.", bullet_style))

    story.append(Paragraph("11.3 Resolution Confirmation", h2_style))
    story.append(Paragraph("• AI/admin proposes a resolution &rarr; Ticket enters <code>RESOLVED_PENDING_CONFIRMATION</code>.", bullet_style))
    story.append(Paragraph("• Customer is explicitly asked whether the issue is fixed.", bullet_style))
    story.append(Paragraph("• <b>YES</b> &rarr; record confirmation &rarr; <code>CLOSED</code> &rarr; CSAT feedback.", bullet_style))
    story.append(Paragraph("• <b>NO</b> &rarr; <code>REOPENED</code> / <code>HUMAN_ESCALATION</code> &rarr; support queue.", bullet_style))

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
    story.append(Paragraph("• Drill down from region &rarr; incident &rarr; complaint list.", bullet_style))
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

    story.append(Paragraph("14.1 Diagnostic Workflow", h2_style))
    story.append(Paragraph("Customer requests speed test &rarr; Backend inspects customer region & active incidents &rarr; Returns telemetry payload &rarr; Rendered as visual diagnostic card in chat &rarr; Read out via bilingual TTS audio.", body_style))
    story.append(PageBreak())

    # ================= PAGE 16 =================
    story.append(Paragraph("15. Backend REST API Specifications", h1_style))
    api_data = [
        [Paragraph("Method & Route", table_header_style), Paragraph("Role", table_header_style), Paragraph("Purpose & Functionality", table_header_style)],
        [Paragraph("POST /api/auth/login", table_cell_bold), Paragraph("Public", table_cell_style), Paragraph("Customer/admin authentication; returns signed JWT.", table_cell_style)],
        [Paragraph("POST /api/auth/signup", table_cell_bold), Paragraph("Public", table_cell_style), Paragraph("Customer self-registration with region and service.", table_cell_style)],
        [Paragraph("POST /api/chat", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Conversational endpoint executing LangGraph StateGraph.", table_cell_style)],
        [Paragraph("POST /api/chat/diagnostic", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Executes real-time network speed/latency diagnostics.", table_cell_style)],
        [Paragraph("POST /api/chat/voice", table_cell_bold), Paragraph("Customer", table_cell_style), Paragraph("Multilingual voice transcription via Groq Whisper.", table_cell_style)],
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
    story.append(Paragraph("• Signed JWT authentication on all protected routes.<br/>"
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
        [Paragraph("Speech Recognition", table_cell_bold), Paragraph("Groq Whisper", table_cell_style), Paragraph("Multilingual voice complaint transcription (Zero cost).", table_cell_style)],
        [Paragraph("Embeddings", table_cell_bold), Paragraph("sentence-transformers", table_cell_style), Paragraph("all-MiniLM-L6-v2 local CPU embeddings (Zero cost).", table_cell_style)],
        [Paragraph("Vector Store", table_cell_bold), Paragraph("ChromaDB (local)", table_cell_style), Paragraph("Persistent vector store for SOP retrieval (Zero cost).", table_cell_style)],
        [Paragraph("Multilingual Tokenizer", table_cell_bold), Paragraph("Hugging Face DistilBERT", table_cell_style), Paragraph("distilbert-base-multilingual-cased (Zero cost).", table_cell_style)],
        [Paragraph("Classification & ML", table_cell_bold), Paragraph("scikit-learn", table_cell_style), Paragraph("Complaint category and intent classification (Zero cost).", table_cell_style)],
        [Paragraph("Database", table_cell_bold), Paragraph("SQLite (local)", table_cell_style), Paragraph("Live operational state in WAL mode (Zero cost).", table_cell_style)],
        [Paragraph("Backend", table_cell_bold), Paragraph("Python + FastAPI", table_cell_style), Paragraph("REST API and background scheduler (Zero cost).", table_cell_style)],
        [Paragraph("Geocoding", table_cell_bold), Paragraph("Geoapify (Free tier)", table_cell_style), Paragraph("Location coordinates with memory cache (Zero cost).", table_cell_style)],
    ]
    story.append(make_table(cost_data, [110, 130, 264]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("16.1 Deterministic Offline Fallbacks & Cost Statement", h2_style))
    story.append(Paragraph(
        "<b>Target is $0 software/API spend for the hackathon demo.</b> Every external API call includes an immediate "
        "deterministic offline fallback, guaranteeing that the entire application operates and all automated tests pass "
        "even with no API keys or internet connection.", body_style))
    story.append(PageBreak())

    # ================= PAGE 18 =================
    story.append(Paragraph("17. Non-Functional Requirements", h1_style))
    nfr_data = [
        [Paragraph("Category", table_header_style), Paragraph("Requirement & Implemented Standard", table_header_style)],
        [Paragraph("Performance", table_cell_bold), Paragraph("Customer/API interaction latency <= 1.5s on live Groq LLM, <= 50ms on offline fallback.", table_cell_style)],
        [Paragraph("Availability", table_cell_bold), Paragraph("Ticket/status operations remain 100% usable even if external LLM is offline.", table_cell_style)],
        [Paragraph("Security", table_cell_bold), Paragraph("Scrypt password hashing, signed JWT tokens, role-based authorization guards.", table_cell_style)],
        [Paragraph("Privacy", table_cell_bold), Paragraph("Automatic regex PII redaction of names, phone numbers, and emails upon ingestion.", table_cell_style)],
        [Paragraph("Reliability", table_cell_bold), Paragraph("Deterministic SQLite database transactions; AI failures never create invalid states.", table_cell_style)],
        [Paragraph("Explainability", table_cell_bold), Paragraph("AI classification, priority scores, and root causes expose contributing factors and evidence.", table_cell_style)],
        [Paragraph("Auditability", table_cell_bold), Paragraph("All status, assignment, resolution, escalation and notification actions are logged immutably.", table_cell_style)],
        [Paragraph("Language", table_cell_bold), Paragraph("Full bidirectional English, Hindi (Devanagari), and Hinglish transliteration support.", table_cell_style)],
        [Paragraph("Cost", table_cell_bold), Paragraph("100% free-tier architecture with zero cloud infrastructure overhead.", table_cell_style)],
    ]
    story.append(make_table(nfr_data, [100, 404]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("17.1 AI Safety Rules", h2_style))
    story.append(Paragraph("• Never fabricate live ticket status or ticket IDs.<br/>"
                           "• Never claim an outage is confirmed when it is only an unverified AI hypothesis.<br/>"
                           "• Never claim resolution without explicit customer confirmation.<br/>"
                           "• Never reveal another customer's private data.<br/>"
                           "• Never perform privileged database actions directly from generated text.<br/>"
                           "• When confidence or evidence is insufficient, ask clarification or escalate.", body_style))
    story.append(PageBreak())

    # ================= PAGE 19 =================
    story.append(Paragraph("18. Recommended Technology Stack", h1_style))
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology Choice & Version", table_header_style)],
        [Paragraph("Customer UI", table_cell_bold), Paragraph("React 18/19, Vite, 40/60 Split Layout, Theme Engine (Dark/Light mode).", table_cell_style)],
        [Paragraph("Admin Dashboard", table_cell_bold), Paragraph("React + Leaflet + React-Leaflet + Recharts + Admin AI Assistant.", table_cell_style)],
        [Paragraph("Backend", table_cell_bold), Paragraph("Python 3.10+ + FastAPI + Uvicorn.", table_cell_style)],
        [Paragraph("Database", table_cell_bold), Paragraph("SQLite 3 with WAL Mode (tci.db).", table_cell_style)],
        [Paragraph("Vector Store", table_cell_bold), Paragraph("ChromaDB Persistent Client (backend/data/chroma_db).", table_cell_style)],
        [Paragraph("Embeddings", table_cell_bold), Paragraph("Sentence Transformers (all-MiniLM-L6-v2).", table_cell_style)],
        [Paragraph("Multilingual NLP", table_cell_bold), Paragraph("Hugging Face Transformers (distilbert-base-multilingual-cased).", table_cell_style)],
        [Paragraph("LLM & Speech", table_cell_bold), Paragraph("Groq Cloud API (Llama-3.3-70b, Llama-3.1-8b, Whisper-large-v3-turbo).", table_cell_style)],
        [Paragraph("Geocoding", table_cell_bold), Paragraph("Geoapify Geocoding REST API (Cached).", table_cell_style)],
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
        [Paragraph("FastAPI", table_cell_bold), Paragraph("Authorize and execute state transitions.", table_cell_style), Paragraph("Depend on LLM text for authorization.", table_cell_style)],
        [Paragraph("Admin Dashboard", table_cell_bold), Paragraph("Operate, monitor, and approve broadcasts.", table_cell_style), Paragraph("Bypass backend authorization or audit logs.", table_cell_style)],
    ]
    story.append(make_table(sep_data, [95, 195, 214]))
    story.append(PageBreak())

    # ================= PAGE 20 =================
    story.append(Paragraph("19. Testing & Acceptance Criteria", h1_style))
    test_scenarios = [
        [Paragraph("Scenario", table_header_style), Paragraph("Acceptance Criteria", table_header_style)],
        [Paragraph("New complaint", table_cell_bold), Paragraph("Customer describes issue &rarr; assistant collects details &rarr; customer verifies &rarr; ticket created.", table_cell_style)],
        [Paragraph("Known outage", table_cell_bold), Paragraph("Assistant identifies matching incident &rarr; links complaint &rarr; avoids unnecessary duplicate ticket.", table_cell_style)],
        [Paragraph("RAG troubleshooting", table_cell_bold), Paragraph("Assistant retrieves approved SOP &rarr; customer performs steps &rarr; confirmation requested.", table_cell_style)],
        [Paragraph("Unresolved issue", table_cell_bold), Paragraph("Customer rejects fix &rarr; complaint reopens/escalates &rarr; support queue receives ticket.", table_cell_style)],
        [Paragraph("Status check", table_cell_bold), Paragraph("Customer asks status &rarr; current DB state returned, not stale model memory.", table_cell_style)],
        [Paragraph("Admin update", table_cell_bold), Paragraph("Admin changes status &rarr; customer sees updated state on next request/notification.", table_cell_style)],
        [Paragraph("Spike detection", table_cell_bold), Paragraph("Synthetic complaint burst &rarr; abnormality detected &rarr; incident appears on dashboard.", table_cell_style)],
        [Paragraph("Root cause", table_cell_bold), Paragraph("Dashboard shows hypothesis with evidence bullets and confidence gauge (90%+).", table_cell_style)],
        [Paragraph("Authorization", table_cell_bold), Paragraph("Customer cannot read another customer's complaint even with its ticket ID.", table_cell_style)],
        [Paragraph("AI outage", table_cell_bold), Paragraph("Groq unavailable &rarr; deterministic status/ticket APIs still work with offline fallbacks.", table_cell_style)],
    ]
    story.append(make_table(test_scenarios, [120, 384]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("19.1 Key KPIs & Validated Benchmarks", h2_style))
    story.append(Paragraph("• <b>Complaint classification macro-F1:</b> >= 82.4% (Exceeds >= 80% target on held-out split).<br/>"
                           "• <b>Intent routing accuracy:</b> >= 95.0% across 15+ supported test intents.<br/>"
                           "• <b>Ticket creation correctness:</b> 100% in automated workflow tests.<br/>"
                           "• <b>Status retrieval correctness:</b> 100% in authorized customer tests.<br/>"
                           "• <b>Resolution confirmation capture:</b> 100% of AI-assisted resolution attempts.<br/>"
                           "• <b>Test suite pass rate:</b> 100% (106+ passing tests in <code>backend/tests/</code>).", body_style))
    story.append(PageBreak())

    # ================= PAGE 21 =================
    story.append(Paragraph("20. Implementation Plan & Demo", h1_style))
    plan_phases = [
        [Paragraph("Phase", table_header_style), Paragraph("Implementation Milestone", table_header_style)],
        [Paragraph("1", table_cell_bold), Paragraph("SQLite schema + authentication + role-based access + demo accounts.", table_cell_style)],
        [Paragraph("2", table_cell_bold), Paragraph("FastAPI complaint/status APIs + universal CSV schema-mapper + audit logging.", table_cell_style)],
        [Paragraph("3", table_cell_bold), Paragraph("LangGraph customer assistant + conversation state + intent routing + DistilBERT.", table_cell_style)],
        [Paragraph("4", table_cell_bold), Paragraph("Complaint verification + ticket creation + live status tracking + line speed diagnostic.", table_cell_style)],
        [Paragraph("5", table_cell_bold), Paragraph("ChromaDB vector store + SentenceTransformers + SOP troubleshooting workflow.", table_cell_style)],
        [Paragraph("6", table_cell_bold), Paragraph("Resolution confirmation + confirm-to-close loop + reopen + escalation.", table_cell_style)],
        [Paragraph("7", table_cell_bold), Paragraph("Admin dashboard queue + ticket drawer + team assignment.", table_cell_style)],
        [Paragraph("8", table_cell_bold), Paragraph("Leaflet heatmap + Geoapify geocoding + spike detection + incident management.", table_cell_style)],
        [Paragraph("9", table_cell_bold), Paragraph("Root-cause investigator + evidence dossier panel + confidence gauge.", table_cell_style)],
        [Paragraph("10", table_cell_bold), Paragraph("Proactive notification queue + admin approval + in-app notification feed.", table_cell_style)],
        [Paragraph("11", table_cell_bold), Paragraph("LangGraph Admin AI Assistant + prompt chips + decision support cockpit.", table_cell_style)],
        [Paragraph("12", table_cell_bold), Paragraph("Theme engine (Dark/Light), multilingual voice STT/TTS, full test suite validation.", table_cell_style)],
    ]
    story.append(make_table(plan_phases, [45, 459]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("20.1 Minimum Successful Demo", h2_style))
    story.append(Paragraph("• Customer reports a broadband/network problem in natural language (English/Hindi/Hinglish).<br/>"
                           "• Assistant verifies details and checks whether the region has an active incident.<br/>"
                           "• Known issue is handled through incident explanation or ChromaDB RAG troubleshooting.<br/>"
                           "• Unresolved complaint becomes a ticket with P1-P4 priority score and SLA countdown.<br/>"
                           "• Admin updates the ticket; customer sees the update in real time.<br/>"
                           "• Customer rejects an attempted resolution; ticket reopens/escalates.<br/>"
                           "• Outage spike appears on the Leaflet heatmap in red.<br/>"
                           "• System creates an incident and generates an evidence-backed root-cause dossier.<br/>"
                           "• Admin reviews/approves a proactive broadcast customer notification.<br/>"
                           "• Admin queries the Operations AI Assistant for decision support.", body_style))
    story.append(PageBreak())

    # ================= PAGE 22 =================
    story.append(Paragraph("21. Product Differentiation", h1_style))
    diff_data = [
        [Paragraph("Traditional Complaint System", table_header_style), Paragraph("Proposed TelConnect Platform", table_header_style)],
        [Paragraph("Collects complaint and creates passive ticket.", table_cell_bold), Paragraph("Understands complaint and attempts autonomous grounded resolution.", table_cell_style)],
        [Paragraph("Customer waits for support.", table_cell_bold), Paragraph("Assistant provides immediate line diagnostics & grounded SOP troubleshooting.", table_cell_style)],
        [Paragraph("Ticket status is opaque.", table_cell_bold), Paragraph("Customer has live status, assigned team, SLA countdown and full history.", table_cell_style)],
        [Paragraph("Agent marks resolved unilaterally.", table_cell_bold), Paragraph("Customer explicitly confirms resolution (confirm-to-close loop); rejected fixes reopen.", table_cell_style)],
        [Paragraph("CSV/dataset is primary data source.", table_cell_bold), Paragraph("Database is dynamic SQLite; CSV is only a seed/analysis source.", table_cell_style)],
        [Paragraph("Dashboard is mainly passive reporting.", table_cell_bold), Paragraph("Dashboard is an operational control plane with LangGraph AI Assistant.", table_cell_style)],
        [Paragraph("Outages discovered after many calls.", table_cell_bold), Paragraph("Complaint spikes trigger real-time anomaly alerts & root-cause dossiers.", table_cell_style)],
        [Paragraph("Generic AI chatbot.", table_cell_bold), Paragraph("Controlled LangGraph multi-task orchestrator connected to real APIs.", table_cell_style)],
    ]
    story.append(make_table(diff_data, [230, 274]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("21.1 Final Product Definition", h2_style))
    story.append(Paragraph(
        "<b>A customer-first AI complaint resolution platform that combines conversational support, dynamic network "
        "diagnostics, automated troubleshooting, live ticket management, customer verification and resolution confirmation "
        "with telecom operational intelligence such as classification, sentiment, escalation prediction, duplicate detection, "
        "geographic heatmaps, complaint spike detection, AI-assisted root-cause analysis and proactive incident notification.</b>", body_style))
    story.append(PageBreak())

    # ================= PAGE 23 =================
    story.append(Paragraph("22. Recommended Presentation Flow", h1_style))
    pres_data = [
        [Paragraph("Scene", table_header_style), Paragraph("Demonstration", table_header_style), Paragraph("Message to Judges", table_header_style)],
        [Paragraph("Customer problem", table_cell_bold), Paragraph("Customer reports telecom issue in Hindi/Hinglish.", table_cell_style), Paragraph("AI understands intent in any language.", table_cell_style)],
        [Paragraph("Line diagnostic", table_cell_bold), Paragraph("Customer triggers on-demand speed test.", table_cell_style), Paragraph("Real-time network telemetry inside chat.", table_cell_style)],
        [Paragraph("Intelligence", table_cell_bold), Paragraph("Assistant detects category, sentiment, urgency.", table_cell_style), Paragraph("Complaint intelligence happens immediately.", table_cell_style)],
        [Paragraph("Resolution", table_cell_bold), Paragraph("RAG provides troubleshooting or incident info.", table_cell_style), Paragraph("AI tries to solve before escalating.", table_cell_style)],
        [Paragraph("Ticket", table_cell_bold), Paragraph("Unresolved case becomes structured P1-P4 ticket.", table_cell_style), Paragraph("No complaint is lost.", table_cell_style)],
        [Paragraph("Tracking", table_cell_bold), Paragraph("Customer asks for status later.", table_cell_style), Paragraph("Live dynamic backend single source of truth.", table_cell_style)],
        [Paragraph("Confirmation", table_cell_bold), Paragraph("Customer accepts (Yes ✓) or rejects fix.", table_cell_style), Paragraph("Closed-loop customer experience.", table_cell_style)],
        [Paragraph("Admin Cockpit", table_cell_bold), Paragraph("Support team sees and operates the same ticket.", table_cell_style), Paragraph("Zero data drift across surfaces.", table_cell_style)],
        [Paragraph("Mass issue", table_cell_bold), Paragraph("Complaint spike appears on Leaflet heatmap.", table_cell_style), Paragraph("System sees network patterns.", table_cell_style)],
        [Paragraph("Root cause", table_cell_bold), Paragraph("AI provides evidence-backed dossier (92%).", table_cell_style), Paragraph("Actionable explainable intelligence.", table_cell_style)],
        [Paragraph("Proactive alert", table_cell_bold), Paragraph("Notification is approved for affected users.", table_cell_style), Paragraph("Human-in-the-loop reduces duplicates.", table_cell_style)],
        [Paragraph("Ops AI Assistant", table_cell_bold), Paragraph("Admin queries NOC operations agent.", table_cell_style), Paragraph("Executive decision support cockpit.", table_cell_style)],
    ]
    story.append(make_table(pres_data, [95, 205, 204]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("23. Requirements Traceability to Use Case 13", h1_style))
    req_map = [
        [Paragraph("Use Case Requirement", table_header_style), Paragraph("PRD Implementation Details", table_header_style)],
        [Paragraph("Classify complaint categories", table_cell_bold), Paragraph("TF-IDF + Logistic Regression (Macro-F1 >= 82.4%).", table_cell_style)],
        [Paragraph("Detect customer sentiment", table_cell_bold), Paragraph("Sentiment Analysis & negative urgency weighting.", table_cell_style)],
        [Paragraph("Prioritize critical complaints", table_cell_bold), Paragraph("Multi-Factor Priority Scoring + Admin Queue + SLA deadlines.", table_cell_style)],
        [Paragraph("Predict escalation risk", table_cell_bold), Paragraph("Escalation Risk model (churn & regulatory threats) + alerts.", table_cell_style)],
        [Paragraph("Recommend resolution actions", table_cell_bold), Paragraph("ChromaDB Vector RAG + approved SOP procedures.", table_cell_style)],
        [Paragraph("Generate ticket summaries", table_cell_bold), Paragraph("Groq LLM / template fallback summary stored with complaint.", table_cell_style)],
        [Paragraph("Complaint triage assistant", table_cell_bold), Paragraph("LangGraph 6-node Customer Multi-Task StateGraph.", table_cell_style)],
        [Paragraph("Vector DB / RAG", table_cell_bold), Paragraph("ChromaDB persistent vector store + SentenceTransformers.", table_cell_style)],
        [Paragraph("Root-cause / intelligence", table_cell_bold), Paragraph("Spike detection + Leaflet heatmap + Root-Cause Investigator.", table_cell_style)],
        [Paragraph("Operations AI decision support", table_cell_bold), Paragraph("LangGraph Admin Operations Agent (/admin/assistant).", table_cell_style)],
        [Paragraph("Customer experience", table_cell_bold), Paragraph("40/60 Split chat, line diagnostics, confirm-to-close loop.", table_cell_style)],
    ]
    story.append(make_table(req_map, [150, 354]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("24. Conclusion & Appendix", h1_style))
    story.append(Paragraph(
        "This PRD defines a complete, professional product rather than a collection of disconnected AI features. "
        "The customer assistant understands and resolves individual problems; the shared SQLite backend guarantees live "
        "complaint state; the admin dashboard manages operations; and the intelligence layer turns complaint patterns into "
        "proactive service insights.", body_style))
    story.append(Paragraph(
        "<b>The strongest demonstration of the product is therefore not 'the chatbot can answer a complaint.' It is: 'The "
        "system understands the complaint, tries to resolve it, creates and tracks a real ticket when needed, verifies the "
        "customer's resolution, and simultaneously learns from complaint patterns to detect and prevent larger telecom "
        "problems.'</b>", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Appendix — Provider / API Note:</b> Groq Cloud API operates within published free-tier rate limits with OpenAI-compatible endpoints. All features include deterministic offline fallbacks ensuring 100% resilience with zero API key dependencies.", body_style))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_path}")


if __name__ == "__main__":
    build_new_prd_pdf(NEW_PRD_PDF_DOCS)
    build_new_prd_pdf(NEW_PRD_PDF_ROOT)
