"""Synthetic seed data — a complete, demo-ready telecom complaint story.

The generated Complaints.csv tells THREE stories at once, so every feature has
something impressive to show:

1. HEADLINE SPIKE — Raj Nagar, Ghaziabad: 4x+ burst of broadband hard-down complaints
   in the last 6 hours. Heatmap goes red, spike alert fires, root cause reads
   "node disruption" (matches past incident INC-2025-0873 in the knowledge base),
   notifications draft for the Raj Nagar broadband customers.
2. CONTRAST CLUSTER — Gurgaon Sector 29: evening mobile-data congestion building over
   days (slow-speed complaints, not hard-down). Opens a second, smaller incident whose
   evidence profile differs, so the Root-Cause Investigator visibly distinguishes
   "congestion" from "node failure" — the explainability money-shot.
3. ESCALATION DRAMA — a spread of high-risk complaints (TRAI threats, churn threats,
   repeat contacts) across regions, so the risk table shows varied, explainable factors.

Resolved rows carry realistic resolution notes — they feed the RAG knowledge base, so the
assistant can cite real past tickets. Timestamps are generated relative to NOW on every
backend start, so the demo is always "live today", never stale.
"""
import csv
import os
import random
import time
from datetime import datetime, timedelta, timezone

from . import db
from .controllers import auth

REGIONS = {
    "Raj Nagar, Ghaziabad":   (28.6926, 77.4383),
    "Indirapuram, Ghaziabad": (28.6420, 77.3724),
    "Connaught Place, Delhi": (28.6315, 77.2167),
    "Dwarka, Delhi":          (28.5921, 77.0460),
    "Gurgaon Sector 29":      (28.4595, 77.0266),
    "Noida Sector 62":        (28.6270, 77.3649),
    "Andheri, Mumbai":        (19.1136, 72.8697),
    "Bandra, Mumbai":         (19.0596, 72.8295),
    "Koramangala, Bangalore": (12.9352, 77.6245),
    "Whitefield, Bangalore":  (12.9698, 77.7500),
    "T Nagar, Chennai":       (13.0418, 80.2341),
    "Salt Lake, Kolkata":     (22.5867, 88.4171),
}

# (template, category, service_type) — English / Hindi / Hinglish mix per PRD
TEMPLATES = [
    ("Broadband has been down since {t} in my area, no connectivity at all", "network", "broadband"),
    ("Internet not working since morning, router shows red light", "network", "broadband"),
    ("Net nahi chal raha hai subah se, kaam ruk gaya hai please fix", "network", "broadband"),
    ("Wifi keeps disconnecting every few minutes, work from home impossible", "network", "broadband"),
    ("Frequent call drops when talking for more than 2 minutes", "network", "voice"),
    ("Call quality bahut kharab hai, awaaz cut hoti rehti hai", "network", "voice"),
    ("Mobile data extremely slow, pages take forever to load on 4G", "network", "mobile data"),
    ("4G speed ekdum slow ho gaya hai is week, barely 1 mbps", "network", "mobile data"),
    ("No signal inside my house since yesterday evening", "network", "voice"),
    ("I was charged twice for my monthly plan, need refund immediately", "billing", "broadband"),
    ("Bill me extra charges laga diye hain jo maine use nahi kiya", "billing", "mobile data"),
    ("My recharge of 599 not reflecting but money deducted from bank", "billing", "mobile data"),
    ("International roaming pack charged but never activated", "billing", "voice"),
    ("Autopay deducted twice this month, very frustrating experience", "billing", "broadband"),
    ("Wrong late fee added even though I paid before the due date", "billing", "broadband"),
    ("Requested plan upgrade a week ago, still not activated", "service", "broadband"),
    ("New connection installation pending for 10 days despite payment", "service", "broadband"),
    ("SIM porting request pending since last week, when will it complete", "service", "voice"),
    ("Naya connection ke liye 2 hafte se wait kar raha hoon, koi response nahi", "service", "broadband"),
    ("Technician never showed up for the scheduled visit, no call either", "service", "broadband"),
    ("My router provided by company keeps restarting every hour", "device", "broadband"),
    ("Set top box remote not working, need replacement", "device", "other"),
    ("Company ka diya hua modem baar baar hang ho raha hai", "device", "broadband"),
    ("5G not working on my new phone even though plan supports it", "device", "mobile data"),
    ("ONT box blinking red, replacement needed urgently", "device", "broadband"),
    ("App login not working, OTP never arrives", "other", "other"),
    ("Want to know about family plan options and pricing", "other", "other"),
    ("Need GST invoice for my corporate connection", "other", "other"),
]

# realistic closure notes per category — resolved rows feed the RAG knowledge base
RESOLUTIONS = {
    "network": [
        "Node rebooted at local exchange; connectivity restored and confirmed with customer.",
        "VoLTE re-provisioned on the SIM and phone rebooted; call drops stopped.",
        "APN reset to default and cell congestion cleared after RF team added capacity; speeds normal.",
        "Fiber patch re-spliced at the junction box; link stable for 24 hours, ticket closed.",
    ],
    "billing": [
        "Duplicate payment reversed to source account in 5 business days; customer confirmed receipt.",
        "Incorrect charge waived and adjusted in next invoice; goodwill credit of Rs 50 applied.",
        "Payment reconciliation job re-run with the transaction ID; recharge credited same day.",
        "Late fee reversed after payment date verification; autopay mandate corrected.",
    ],
    "service": [
        "Installation escalated to area field manager; completed next day, customer confirmed.",
        "Porting request re-submitted with corrected UPC code; number active on new plan.",
        "Plan upgrade applied manually and prorated; confirmation SMS sent.",
        "Technician visit rescheduled with slot confirmation; work completed on second visit.",
    ],
    "device": [
        "Faulty router replaced under warranty; new unit delivered and activated in 2 days.",
        "Set top box remote replaced free of cost; paired and verified working.",
        "Overheating modem swapped; advised customer on ventilation, stable since.",
        "SIM replaced at store; 5G registering correctly on the handset now.",
    ],
    "other": [
        "OTP delivery restored after SMS gateway fix; customer logged in successfully.",
        "Shared family plan options and activated chosen 4-line plan on request.",
        "GST invoice generated and emailed; billing profile updated with GSTIN.",
    ],
}

# high-drama complaints — populate the escalation-risk table with varied, explainable factors
DRAMA = [
    ("This is the third time I am complaining about the same billing error, still no refund. "
     "If it is not fixed this week I am filing a TRAI complaint.", "billing", "broadband"),
    ("Internet down AGAIN and customer care disconnected my call twice. I am seriously "
     "considering porting to another provider, last chance.", "network", "broadband"),
    ("No technician visit for 12 days despite daily calls. Pathetic service, I will take this "
     "to consumer court if not resolved immediately.", "service", "broadband"),
    ("Baar baar complaint karne ke baad bhi koi response nahi. Bahut kharab experience, "
     "main apna number port kara raha hoon.", "service", "voice"),
    ("You charged me for a plan I cancelled last month. This is fraud — refund immediately or "
     "I am reporting to the ombudsman.", "billing", "mobile data"),
    ("Second router replacement in a month and it still keeps restarting. Useless hardware, "
     "cancel my connection if this is not fixed.", "device", "broadband"),
    ("My elderly parents have had no working phone line for 4 days. This is an emergency, "
     "escalate right now.", "network", "voice"),
    ("Still waiting on last week's complaint, nobody called back. Worst customer service, "
     "switching to Airtel this weekend.", "service", "mobile data"),
]

CHANNELS = ["call", "chat", "app", "email", "social"]
NETWORKS = ["2G", "3G", "4G", "5G", "fiber"]
DEVICES = ["Samsung Galaxy S23", "iPhone 14", "OnePlus 11", "Xiaomi 13", "TP-Link Router", "JioFiber ONT", ""]
FIRSTS = ["Aarav", "Vivaan", "Aditya", "Ananya", "Diya", "Ishaan", "Kavya", "Rohan", "Priya", "Arjun",
          "Sneha", "Rahul", "Pooja", "Karan", "Meera", "Nikhil", "Riya", "Sameer", "Tanvi", "Varun"]
LASTS = ["Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Reddy", "Iyer", "Das", "Joshi"]

SOP_DOCS = [
    ("Router red light / no sync", "network",
     "Symptom: broadband down, router DSL/LOS light red or blinking. Known fix: power off the router "
     "for 60 seconds, then restart. If the red light persists, check the fiber cable is firmly clicked in. "
     "If still down and neighbours are also affected, it is a node/line fault - register a ticket; "
     "typical resolution is a node reboot or fiber splice within 4-6 hours."),
    ("Slow mobile data on 4G/5G", "network",
     "Symptom: very slow mobile data despite full signal. Known fix: toggle airplane mode for 10 seconds, "
     "verify APN is set to default, and check daily data quota is not exhausted. If speed stays under "
     "1 Mbps in one locality, it indicates cell congestion - register a ticket for the RF team."),
    ("Frequent call drops", "network",
     "Symptom: calls drop after 1-2 minutes. Known fix: enable VoLTE in SIM settings and reboot the phone. "
     "If drops persist in one location, a tower handover fault is likely - register a ticket."),
    ("Double charge / duplicate billing", "billing",
     "Symptom: charged twice for the same plan or autopay deducted twice. Known fix: duplicate payment "
     "auto-reverses within 5-7 business days to the source account. If it has been longer, register a "
     "ticket with the transaction IDs; billing team issues a manual refund in 48 hours."),
    ("Recharge success but not reflecting", "billing",
     "Symptom: money deducted, plan not active. Known fix: wait 30 minutes, then reboot the phone. "
     "If still not reflecting, register a ticket with the payment reference number - the payment "
     "reconciliation job credits it, usually the same day."),
    ("OTP not arriving in app", "other",
     "Symptom: login OTP never arrives. Known fix: check SMS inbox is not full, disable any SMS-blocking "
     "app, and retry after 15 minutes. OTP delivery can be delayed during network incidents in your area."),
    ("Router keeps restarting", "device",
     "Symptom: company router restarts every few minutes/hours. Known fix: use the original power adapter "
     "and a stable socket; overheating is the top cause - keep vents clear. If it persists, the unit is "
     "likely faulty; register a ticket for a replacement (delivered in 2-3 days)."),
    ("New connection / plan change delayed", "service",
     "Symptom: installation or plan upgrade pending beyond promised date. Known fix: none self-service - "
     "register a ticket; installation SLA is 7 days and a ticket escalates it to the area field manager."),
]

PAST_INCIDENT_WRITEUPS = [
    ("INC-2025-0873 Raj Nagar node failure", "network",
     "Incident INC-2025-0873 (2025-11-04): 4x spike of broadband connectivity complaints in "
     "Raj Nagar, Ghaziabad within 3 hours. Root cause: OLT network node power supply failure at the "
     "Raj Nagar exchange. Resolution: node reboot and PSU replacement; service restored in 5 hours. "
     "Signature: >80% complaints same area, >90% mention no connectivity, sudden onset."),
    ("INC-2025-0912 Andheri fiber cut", "network",
     "Incident INC-2025-0912 (2025-12-19): broadband outage cluster in Andheri, Mumbai after road works. "
     "Root cause: backbone fiber cut. Resolution: splicing crew, restored in 8 hours. "
     "Signature: hard-down complaints concentrated along one corridor, zero throughput."),
    ("INC-2026-0107 Gurgaon cell congestion", "network",
     "Incident INC-2026-0107 (2026-02-02): slow mobile data complaints in Gurgaon Sector 29 every "
     "evening for a week. Root cause: 4G cell congestion after a new residential tower filled in. "
     "Resolution: carrier aggregation enabled + new sector added. Signature: slow-speed (not hard-down) "
     "complaints, evening peaks, gradual drift not sudden spike."),
]


def generate_csv(path: str, n: int = 1300, seed: int = 42) -> str:
    """Write a messy, realistically-columned telecom complaints CSV (tests schema mapping too)."""
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    rows = []
    regions = list(REGIONS)

    def mk_row(region, template, when, status=None, resolution=""):
        text, cat, svc = template
        lat, lng = REGIONS[region]
        name = f"{rng.choice(FIRSTS)} {rng.choice(LASTS)}"
        phone = f"+91-98{rng.randint(10000000, 99999999)}"
        status = status or rng.choices(["resolved", "open", "in_progress"], weights=[55, 35, 10])[0]
        if status == "resolved" and not resolution:
            resolution = rng.choice(RESOLUTIONS[cat])
        return {
            "Ticket ID": f"T{rng.randint(100000, 999999)}",
            "Customer Name": name,
            "Contact Number": phone,
            "Complaint Description": text.format(t=rng.choice(["morning", "last night", "2 hours", "yesterday"])),
            "Complaint Channel": rng.choice(CHANNELS),
            "Created Date": when.strftime("%d-%m-%Y %H:%M"),
            "City Area": region,
            "Latitude": round(lat + rng.uniform(-0.01, 0.01), 5),
            "Longitude": round(lng + rng.uniform(-0.01, 0.01), 5),
            "Service": svc,
            "Network Tech": rng.choice(NETWORKS),
            "Handset Model": rng.choice(DEVICES),
            "Current Status": status,
            "Resolution Notes": resolution,
        }

    # ---- story 0: 30 days of normal background volume everywhere ----
    for _ in range(n - 320):
        region = rng.choice(regions)
        when = now - timedelta(minutes=rng.randint(6 * 60, 30 * 24 * 60))
        rows.append(mk_row(region, rng.choice(TEMPLATES), when))

    # ---- story 1 (headline): Raj Nagar broadband hard-down burst, last 6 hours ----
    broadband_down = [t for t in TEMPLATES if t[2] == "broadband" and t[1] == "network"]
    for _ in range(180):
        when = now - timedelta(minutes=rng.randint(0, 6 * 60))
        rows.append(mk_row("Raj Nagar, Ghaziabad", rng.choice(broadband_down), when, status="open"))

    # ---- story 2 (contrast): Gurgaon mobile-data congestion, evening drift over 5 days ----
    slow_data = [t for t in TEMPLATES if t[2] == "mobile data" and t[1] == "network"]
    for day in range(5, 0, -1):  # an evening cluster each of the past 5 days (baseline drift)
        for _ in range(6):
            evening = now.replace(hour=19, minute=0, second=0, microsecond=0) - timedelta(days=day)
            when = evening + timedelta(minutes=rng.randint(0, 150))
            rows.append(mk_row("Gurgaon Sector 29", rng.choice(slow_data), when, status="resolved"))
    for _ in range(38):  # tonight it breaches the rolling baseline -> second incident
        when = now - timedelta(minutes=rng.randint(0, 5 * 60))
        rows.append(mk_row("Gurgaon Sector 29", rng.choice(slow_data), when, status="open"))

    # ---- story 3: escalation drama spread across regions and recent days ----
    for text, cat, svc in DRAMA:
        region = rng.choice([r for r in regions if r != "Raj Nagar, Ghaziabad"])
        when = now - timedelta(minutes=rng.randint(3 * 60, 3 * 24 * 60))
        rows.append(mk_row(region, (text, cat, svc), when, status="open"))

    # ---- mild recent activity elsewhere so the heatmap has contrast, not two dots ----
    for _ in range(40):
        region = rng.choice([r for r in regions if r not in ("Raj Nagar, Ghaziabad", "Gurgaon Sector 29")])
        when = now - timedelta(minutes=rng.randint(0, 6 * 60))
        rows.append(mk_row(region, rng.choice(TEMPLATES), when))

    # ---- duplicates: same ticket re-reported on another channel (tests dedupe) ----
    for r in rng.sample(rows, 25):
        dup = dict(r)
        dup["Complaint Channel"] = rng.choice([c for c in CHANNELS if c != r["Complaint Channel"]])
        rows.append(dup)

    rng.shuffle(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def seed_kb() -> None:
    conn = db.connect()
    if conn.execute("SELECT COUNT(*) c FROM kb_docs").fetchone()["c"] > 0:
        return
    for title, cat, body in SOP_DOCS:
        conn.execute(
            "INSERT INTO kb_docs(doc_id,kind,title,body,category,created_at) VALUES(?,?,?,?,?,?)",
            (db.new_id("SOP"), "sop", title, body, cat, db.now_iso()),
        )
    for title, cat, body in PAST_INCIDENT_WRITEUPS:
        conn.execute(
            "INSERT INTO kb_docs(doc_id,kind,title,body,category,created_at) VALUES(?,?,?,?,?,?)",
            (db.new_id("KBI"), "incident_writeup", title, body, cat, db.now_iso()),
        )
    conn.commit()


DEMO_ACCOUNTS = [
    # (name, email, region, service) — password for all: customer123
    ("Rohan Sharma", "rohan@example.com", "Raj Nagar, Ghaziabad", "broadband"),
    ("Arjun Iyer", "arjun@example.com", "Raj Nagar, Ghaziabad", "broadband"),
    ("Tanvi Gupta", "tanvi@example.com", "Raj Nagar, Ghaziabad", "broadband"),
    ("Karan Malhotra", "karan@example.com", "Gurgaon Sector 29", "mobile data"),
    ("Sneha Reddy", "sneha@example.com", "Gurgaon Sector 29", "mobile data"),
    ("Priya Patel", "priya@example.com", "Andheri, Mumbai", "mobile data"),
    ("Nikhil Das", "nikhil@example.com", "Koramangala, Bangalore", "broadband"),
]


def seed_accounts() -> None:
    conn = db.connect()
    if not conn.execute("SELECT 1 FROM users WHERE email=?", ("admin@telecom.com",)).fetchone():
        auth.create_user("admin", "Operations Admin", "admin@telecom.com", "admin123")
    for name, email, region, service in DEMO_ACCOUNTS:
        if not conn.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            auth.create_user("customer", name, email, "customer123",
                             region=region, service_type=service)


CSV_MAX_AGE_SECONDS = 3600  # regenerate hourly so the injected spike is always "right now"


def ensure_seed_files(force: bool = False) -> str:
    """Demo CSV with timestamps relative to now. Regenerated when stale, so the
    spike story is live on demo day no matter when the project was built."""
    data_dir = os.path.dirname(db.DB_PATH)
    csv_path = os.path.join(data_dir, "sample_complaints.csv")
    stale = (not os.path.exists(csv_path)
             or time.time() - os.path.getmtime(csv_path) > CSV_MAX_AGE_SECONDS)
    if force or stale:
        generate_csv(csv_path)
    return csv_path
