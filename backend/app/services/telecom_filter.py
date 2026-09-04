"""Telecom Domain Relevance Filter for TelConnect Chatbots.

Determines whether a user's question or message is related to telecommunications.
Provides the standard domain restriction message for unrelated questions.
"""
import logging
import re
from typing import Optional

from .groq_client import groq_available, groq_chat_messages

logger = logging.getLogger(__name__)

TELECOM_RESTRICTION_MESSAGE = (
    "I'm designed to answer telecom-related questions only. "
    "Please ask me about mobile networks, SIM/eSIM, 4G/5G, calls, SMS, "
    "mobile data, roaming, recharge plans, connectivity, or other telecom services."
)

# Standard pleasantries and conversational confirmations
CONVERSATIONAL_PATTERNS = [
    re.compile(r"(?:^|\s)(hi|hello|hey|namaste|namaskar|good (morning|afternoon|evening|day)|greetings|howdy|kem cho|yo)(?:[\s,!?]|$)", re.I),
    re.compile(r"(?:^|\s)(thank you|thanks|thank u|dhanyawad|shukriya|many thanks|thanks a lot|thx)(?:[\s,!?]|$)", re.I),
    re.compile(r"(?:^|\s)(yes|yeah|yep|y|sure|ok|okay|confirm|haan|ha|correct|please do|go ahead|kardo|done|chal gaya|theek hai|bilkul)(?:[\s,!?]|$)", re.I),
    re.compile(r"(?:^|\s)(no|nope|nahi|nah|na)(?:[\s,!?]|$)", re.I),
    re.compile(r"^\s*[1-5]\s*(?:star|stars|rating)?\s*$", re.I),
    # Devanagari pleasantries
    re.compile(r"(नमस्ते|नमस्कार|प्रणाम|धन्यवाद|शुक्रिया|हाँ|नहीं|ठीक है)"),
]

# Explicit non-telecom queries (general knowledge, coding, math, jokes, poems, biology, world history, etc.)
NON_TELECOM_PATTERNS = [
    # Politics / Leaders / Governance
    re.compile(r"\b(president|prime minister|chief minister|governor|monarch|chancellor|parliament|election|political party|senate|congressman)\b", re.I),
    # Geography / Weather / Capitals / Countries trivia
    re.compile(r"\b(capital of|currency of|population of|weather in|temperature in|recipe for|ingredients for|tallest mountain|longest river|deepest ocean)\b", re.I),
    # Biology / Science / Astronomy
    re.compile(r"\b(photosynthesis|mitochondria|cellular respiration|dna|rna|quantum mechanics|astrophysics|black hole|solar system|planet|galaxy|relativity)\b", re.I),
    # History / Wars
    re.compile(r"\b(world war|french revolution|civil war|historical battle|renaissance|ancient rome|ancient greece|mughal empire|dynasty)\b", re.I),
    # Programming / Coding
    re.compile(r"\b(write (?:a )?(?:python|javascript|java|c\+\+|rust|html|css|sql|react|backend|frontend|code|script|program)|code in (?:python|java|c\+\+|javascript))\b", re.I),
    # Mathematics
    re.compile(r"\b(solve (?:this )?(?:math|mathematics|equation|algebra|integral|calculus|arithmetic|geometry|problem)|calculate the integral|pythagorean)\b", re.I),
    # Entertainment / Humor / Creative
    re.compile(r"\b(tell (?:me )?(?:a )?joke|make me laugh|tell a riddle|riddle me this|knock knock joke)\b", re.I),
    re.compile(r"\b(write (?:a )?(?:poem|poetry|song|lyrics|story|essay|novel|haiku))\b", re.I),
    re.compile(r"\b(movie|actor|actress|bollywood|hollywood|box office|oscar winner|cricket match|ipl score|football match|fifa world cup)\b", re.I),
    # Dictionary definitions of ambiguous or non-telecom generic words
    re.compile(r"^\s*(?:what is the meaning of|meaning of|define|what is|tell me about)\s+(?:edge|life|love|happiness|world|apple|book|table|chair|dog|cat|water|air|sun|moon|car|bus|train|plane|school|university|friend|friendship|money|time|space|art|music|peace|war|a random english word)\??\s*$", re.I),
    # Ambiguous "what is a network" / "what is network" without telecom modifier
    re.compile(r"^\s*(?:what is (?:a |the )?network\??|what is network\??|define network\??|meaning of network\??)\s*$", re.I),
    re.compile(r"\b(?:neural network|social network|social networking|transportation network|road network|biological network)\b", re.I),
    # Hindi non-telecom questions
    re.compile(r"(राष्ट्रपति|प्रधानमंत्री|राजधानी|चुटकुला|कविता|गणित|विश्व युद्ध|प्रकाश संश्लेषण)", re.I),
]

# Explicit telecom indicators (cellular standards, SIM, network equipment, broadband, plans, signals, ops)
TELECOM_INDICATORS = [
    # Cellular Generations & Technologies
    re.compile(r"\b(5g|4g|3g|2g|6g|volte|vowifi|lte|voip|gsm|cdma|gprs|wcdma|hspa|hsdpa|umts)\b", re.I),
    # SIM & Cellular Identity
    re.compile(r"\b(esim|sim card|sim|nanosim|microsim|imsi|imei|apn|msisdn|puk|pin code|sim swap|sim port|mnp|porting)\b", re.I),
    # Mobile Data & Connectivity
    re.compile(r"\b(mobile data|mobile internet|cellular data|data pack|data balance|data booster|data limit|daily data|data rollover|internet|net|wifi|wi-fi)\b", re.I),
    re.compile(r"\b(broadband|fiber|fibre|ftth|fttb|fttc|dsl|adsl|vdsl|cable internet|hotspot|ethernet|optical fiber)\b", re.I),
    re.compile(r"\b(roam\w*|international roaming|national roaming|roaming pack|roaming charge|roaming activation|activate roaming)\b", re.I),
    # Recharge, Plans & Billing
    re.compile(r"\b(recharg\w*|prepaid|postpaid|tariff|talktime|topup|top-up|validity|bill\w*|invoice\w*|refund\w*|deduct\w*|plan\w*|pack\w*|autopay|payment\w*|balance)\b", re.I),
    # Voice, Calls, SMS
    re.compile(r"\b(caller tune|call drop|call drops|call waiting|call forwarding|conference call|sms|mms|incoming call|outgoing call|dial tone|make call\w*|send sms|call\w*)\b", re.I),
    # Signal, Coverage, Hardware
    re.compile(r"\b(signal strength|network signal|network coverage|mobile network|cellular network|phone network|telecom network|cell tower|tower|bts|bsc|msc|enb|gnb|coverage area|coverage|signal weak|weak signal|no signal|signal)\b", re.I),
    re.compile(r"\b(router|modem|ont|olt|set top box|stb|optic fiber|patch cord|pon|lan cable|phone|handset)\b", re.I),
    re.compile(r"\b(telecom|telecommunication|telecommunications|telconnect|isp|trai|dot|spectrum|bandwidth|latency|ping|jitter|packet loss|download speed|upload speed|mbps|gbps|kbps|speed)\b", re.I),
    # Telecom specific edge usage
    re.compile(r"\b(showing edge|edge instead of|edge in telecom|edge computing in telecom|edge network|edge data center|telecom edge)\b", re.I),
    # Diagnostics, Issues & Ticket Operations
    re.compile(r"\b(speed test|line diagnostic|diagnos\w*|complaint\w*|ticket\w*|sla|sla deadline|incident\w*|root cause|escalation risk|priority score|priority label|field ops|noc|network ops|rf team|outage|hotspot|density)\b", re.I),
    # Customer support requests & issues
    re.compile(r"\b(help|support|problem|issue|dikkat|pareshani|error|trouble|samasya|assist\w*|facing|not working|down|slow|disconnect\w*|drop\w*|broken|stuck|glitch|fail\w*|replace\w*|pending|restart|dead|buffering|red light)\b", re.I),
    re.compile(r"\b(human support|human agent|support executive|customer care|speak with support|reopen complaint|reopen ticket|check my ticket|my ticket|ticket status|status|update|track)\b", re.I),
    # Hindi/Hinglish telecom keywords
    re.compile(r"(इंटरनेट|नेटवर्क|नेट|सिम|कॉल|मैसेज|रिचार्ज|डेटा|धीमा|ब्रॉडबैंड|टावर|बैलेंस|कट गया|शिकायत|टिकट|काम नहीं|चल नहीं|kaam nahi|chal nahi|net nahi|speed kam|paisa kata|call nahi|signal nahi|mera internet|mera data|slow net|मदद|समस्या|परेशानी)", re.I),
]


def check_telecom_relevance_llm(query: str) -> Optional[bool]:
    """Call Groq LLM to contextually classify whether query is telecom-related."""
    if not groq_available():
        return None
    try:
        system_prompt = (
            "You are a strict telecom domain classification filter for a telecom provider's AI assistants.\n"
            "Your task is to determine whether the user's question or message is related to telecommunications (telecom).\n\n"
            "TELECOM TOPICS (RETURN 'YES'):\n"
            "- Mobile networks, cellular technology (2G, 3G, 4G, 5G, LTE, VoLTE, VoWiFi, GSM, APN, IMSI, IMEI, towers, coverage)\n"
            "- SIM cards, eSIM, mobile signal, weak signal, call drops, SMS delivery, voice calling, MMS\n"
            "- Mobile data, internet speeds, data balance, prepaid/postpaid recharge plans, telecom billing, tariff, refunds\n"
            "- Broadband, fiber optic internet (FTTH), Wi-Fi routers, modems, ONT, OLT, line diagnostics\n"
            "- Telecom customer support tickets, complaints, telecom NOC operations, network outages, incidents\n"
            "- Telecom concepts in context (e.g. 'Why is my phone showing EDGE instead of 4G?', 'What is edge computing in telecom?', 'What is network coverage?', 'What is APN?')\n"
            "- Customer support requests, troubleshooting, assistance with services, greetings/pleasantries or confirmations (e.g. 'help me with my problem', 'hi', 'thank you', 'yes', 'no')\n\n"
            "NON-TELECOM TOPICS (RETURN 'NO'):\n"
            "- General knowledge, history, world facts, geography, politics, presidents, science, biology (e.g. 'Who is the president of India?', 'What is the capital of France?', 'What is photosynthesis?', 'Tell me about World War 2')\n"
            "- Writing code, math equations, telling jokes, writing poems/stories (e.g. 'Write Python code', 'Solve this math problem', 'Tell me a joke', 'Write a poem')\n"
            "- Dictionary definitions of general English words or ambiguous terms without telecom context (e.g. 'What is the meaning of edge?', 'What is a network?')\n\n"
            "Respond with ONLY 'YES' or 'NO'."
        )
        reply = groq_chat_messages(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"User query: {query}"}],
            fallback="", max_tokens=10, temperature=0.0
        )
        clean = (reply or "").strip().upper()
        if "YES" in clean:
            return True
        if "NO" in clean:
            return False
    except Exception as exc:
        logger.warning(f"[telecom_filter] LLM classification error: {exc}")
    return None


def is_telecom_related(text: str, conversation_state: Optional[dict] = None, is_admin: bool = False, normalized_text: Optional[str] = None) -> bool:
    """Determine whether a query is related to telecommunications.
    
    Combines conversational state tracking, semantic rules, and LLM classification.
    """
    clean = text.strip()
    if not clean:
        return False

    combined_texts = [clean]
    if normalized_text and normalized_text.strip() and normalized_text.strip() != clean:
        combined_texts.append(normalized_text.strip())

    # 1. Active conversation state continuation (e.g. confirming a ticket, rating, fix feedback)
    if conversation_state and isinstance(conversation_state, dict) and conversation_state.get("mode"):
        return True

    # 2. Conversational pleasantries and standard responses
    for t in combined_texts:
        for pattern in CONVERSATIONAL_PATTERNS:
            if pattern.search(t):
                return True

    # 3. Explicit non-telecom patterns (must be rejected unless explicitly telecom-qualified)
    has_non_telecom = False
    for t in combined_texts:
        for pattern in NON_TELECOM_PATTERNS:
            if pattern.search(t):
                has_non_telecom = True
                break
        if has_non_telecom:
            break

    if has_non_telecom:
        # Check if there is an overriding explicit telecom context like "in telecom" or "telecom edge"
        for t in combined_texts:
            if re.search(r"\b(in telecom|telecom|telecommunication|telecommunications|4g|5g|volte|vowifi|sim|esim)\b", t, re.I):
                if not re.search(r"\b(president|prime minister|capital of|photosynthesis|world war|joke|poem|python code|solve .* math)\b", t, re.I):
                    return True
        return False

    # 4. Explicit telecom indicators
    for t in combined_texts:
        for pattern in TELECOM_INDICATORS:
            if pattern.search(t):
                return True

    # 5. Admin operations indicators
    if is_admin:
        for t in combined_texts:
            if re.search(r"\b(attention|critical|urgent|risk|spike|hotspot|summary|overview|action|troubleshoot|procedure|sop|reasoning|classification|why was|why is|explain|region|least|fewest|lowest|highest|count|volume|breakdown|metrics|how many)\b", t, re.I):
                return True

    # 6. LLM contextual classification if available
    llm_decision = check_telecom_relevance_llm(clean)
    if llm_decision is not None:
        return llm_decision

    # 7. Fallback: if query does not match any telecom indicators or intent, reject by default
    return False
