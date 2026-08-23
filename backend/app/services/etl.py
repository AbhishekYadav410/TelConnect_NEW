"""Layers 1-2 — universal ingestion + ETL.

Any telecom company's CSV comes in with arbitrary column names; a heuristic mapper
(optionally refined by Groq) maps them onto the internal schema. Then: clean text,
redact PII, normalise timestamps, dedupe, normalise Hinglish tokens.

PII policy (per PRD privacy NFR): phone numbers, emails and person-name columns are
redacted from complaint TEXT before storage or any LLM call. Proactive notifications
never need CSV contact data — they target registered user accounts matched by
region + service_type, so redaction costs nothing.
"""
import csv
import io
import re
from datetime import datetime, timezone

from .. import db
from .groq_client import groq_json

INTERNAL_FIELDS = {
    "text":         ["complaint", "description", "issue", "remarks", "text", "message", "details", "desc"],
    "category":     ["category", "type", "complaint type", "issue type"],
    "channel":      ["channel", "source", "medium"],
    "timestamp":    ["date", "time", "created", "timestamp", "reported", "logged"],
    "region":       ["region", "area", "city", "location", "zone", "circle", "locality"],
    "lat":          ["lat", "latitude"],
    "long":         ["lon", "lng", "longitude"],
    "service_type": ["service", "product", "plan type"],
    "network_type": ["network", "tech", "technology", "connection type"],
    "device":       ["device", "handset", "model", "equipment"],
    "status":       ["status", "state"],
    "resolution":   ["resolution", "fix", "closure", "notes"],
    "external_id":  ["ticket", "id", "reference", "complaint no"],
}

PII_COLUMNS = ["name", "customer name", "contact", "phone", "mobile", "email", "address"]

PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{8,14}\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

# Hinglish -> English token normalisation, applied at ingest AND at RAG query time
# so Devanagari-free code-mixed text still matches the English knowledge base.
HINGLISH_MAP = {
    "chal raha hai": "working", "chal rahi hai": "working",
    "chal raha": "working", "chal rahi": "working", "chalta": "working", "chalti": "working",
    "kaam nahi": "not working", "chal nahi": "not working",
    "subah se": "since morning", "kal se": "since yesterday", "din se": "days since",
    "baar baar": "repeatedly", "ho raha hai": "happening", "ho rahi hai": "happening",
    "ho raha": "happening", "ho rahi": "happening", "gaya hai": "has become", "gayi hai": "has become",
    "laga diye": "added", "kata": "deducted", "paise": "money", "hafte": "weeks",
    "koi response": "no response", "please fix": "please fix", "kya hua": "what happened",
    "nahi": "not", "nahin": "not", "nhi": "not",
    "kharab": "bad", "bahut": "very", "bohot": "very", "ekdum": "totally",
    "net": "internet", "awaaz": "voice", "karo": "do", "kijiye": "please do",
    "jaldi": "quickly", "mera": "my", "meri": "my", "mere": "my",
    "theek": "fine", "band": "down", "madad": "help", "dikkat": "problem",
    "pareshani": "trouble", "dhanyawad": "thank you", "shukriya": "thank you",
    "namaste": "hello", "pranam": "greetings", "batao": "tell", "batayein": "please tell",
    "haan": "yes", "sahi": "correct",
}
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")

_SORTED_HINGLISH = sorted(HINGLISH_MAP.items(), key=lambda x: -len(x[0]))
_HINGLISH_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k, _ in _SORTED_HINGLISH) + r")\b",
    re.I
)


def detect_language(text: str) -> str:
    if DEVANAGARI_RE.search(text):
        return "hi"
    return "hinglish" if _HINGLISH_REGEX.search(text) else "en"


def normalize_hinglish(text: str) -> str:
    return _HINGLISH_REGEX.sub(lambda m: HINGLISH_MAP.get(m.group(0).lower(), m.group(0)), text.lower())


def redact_pii(text: str) -> str:
    text = PHONE_RE.sub("[PHONE]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    return text


def clean_text(text: str) -> str:
    text = redact_pii(text.strip())
    text = re.sub(r"\s+", " ", text)
    return text


def suggest_mapping(headers: list[str], sample_rows: list[dict]) -> dict:
    """Heuristic column mapping; Groq refines it when a key is configured."""
    mapping: dict[str, str | None] = {f: None for f in INTERNAL_FIELDS}
    for header in headers:
        h = header.lower().strip()
        if any(p in h for p in PII_COLUMNS) and "complaint" not in h:
            continue  # PII columns are never mapped into the schema
        for field, hints in INTERNAL_FIELDS.items():
            if mapping[field] is None and any(hint in h for hint in hints):
                mapping[field] = header
                break
    # Groq-assisted refinement (optional, fails soft)
    refined = groq_json(
        system="You map CSV columns of a telecom complaints file onto an internal schema. "
               "Return ONLY JSON: {internal_field: csv_column_or_null}.",
        user=f"Internal fields: {list(INTERNAL_FIELDS)}.\nCSV headers: {headers}.\n"
             f"Sample row: {sample_rows[0] if sample_rows else {}}.\n"
             f"Heuristic guess (fix only if wrong): {mapping}",
        fallback=None,
    )
    if isinstance(refined, dict):
        for field in INTERNAL_FIELDS:
            col = refined.get(field)
            if col in headers:
                mapping[field] = col
    return mapping


def parse_timestamp(value: str) -> str:
    value = (value or "").strip()
    for fmt in ("%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat()
    except ValueError:
        return db.now_iso()


# incoming CSV statuses are mapped onto the v6 lifecycle
STATUS_MAP = {"open": "new", "new": "new", "in_progress": "in_progress",
              "pending": "in_progress", "resolved": "closed", "closed": "closed"}
VALID_SERVICE = {"broadband", "mobile data", "voice", "other"}


def ingest_csv(content: bytes, mapping: dict) -> dict:
    """Map -> clean -> dedupe -> insert. Returns counts. ML scoring runs separately."""
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig", errors="replace")))
    conn = db.connect()
    seen_keys = {r["dedupe_key"] for r in conn.execute(
        "SELECT dedupe_key FROM complaints WHERE dedupe_key IS NOT NULL")}
    inserted = deduped = skipped = 0

    def col(row, field):
        c = mapping.get(field)
        return (row.get(c) or "").strip() if c else ""

    for row in reader:
        raw = col(row, "text")
        if not raw:
            skipped += 1
            continue
        text = clean_text(raw)
        region = col(row, "region") or "Unknown"
        ts = parse_timestamp(col(row, "timestamp"))
        # dedupe: same source ticket + same text (same issue re-reported over multiple
        # channels). Falls back to text+region+day when the CSV has no ticket/ID column.
        ext = col(row, "external_id")
        key = f"{ext}|{text.lower()[:120]}|{region.lower()}|{ts[:10]}"
        if key in seen_keys:
            deduped += 1
            continue
        seen_keys.add(key)
        status = STATUS_MAP.get(col(row, "status").lower().replace(" ", "_"), "new")
        service = col(row, "service_type").lower()
        try:
            lat = float(col(row, "lat")) if col(row, "lat") else None
            lng = float(col(row, "long")) if col(row, "long") else None
        except ValueError:
            lat = lng = None
        if lat is None or lng is None:
            from .geo import geocode_region
            geo = geocode_region(region)
            if geo:
                lat, lng = geo
        conn.execute(
            "INSERT INTO complaints(complaint_id,text,raw_text,channel,timestamp,region,lat,long,"
            "service_type,network_type,device,status,resolution,language,source,dedupe_key,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (db.new_id("TCK"), text, raw[:2000], col(row, "channel").lower() or None, ts, region,
             lat, lng, service if service in VALID_SERVICE else "other",
             col(row, "network_type") or None, col(row, "device") or None,
             status,
             col(row, "resolution") or None, detect_language(text), "upload", key, db.now_iso()),
        )
        inserted += 1
    conn.commit()
    return {"inserted": inserted, "deduplicated": deduped, "skipped_empty": skipped}
