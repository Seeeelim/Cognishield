import json
import re
from urllib.parse import urlparse


URGENT_KEYWORDS = [
    "urgent", "immediately", "asap", "action required", "verify", "suspended",
    "locked", "password", "reset", "invoice", "payment", "wire", "transfer"
]

AUTHORITY_KEYWORDS = [
    "ceo", "director", "hr", "finance", "it support", "security team", "microsoft", "google"
]

CREDENTIAL_KEYWORDS = [
    "login", "sign in", "verify your account", "confirm your password", "credentials", "credit"
]

SHORTENER_DOMAINS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly"}


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    # simple URL regex
    urls = re.findall(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
    # clean trailing punctuation
    cleaned = [u.rstrip(").,;!\"'") for u in urls]
    return cleaned


def domain_of(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        # remove port
        host = host.split(":")[0]
        return host or None
    except Exception:
        return None


def score_email(subject: str | None, from_addr: str | None, reply_to: str | None, body_text: str | None) -> dict:
    """
    Returns dict with:
    - risk_score (0-100)
    - verdict
    - attack_type
    - manipulation_strategy
    - reasons (list)
    - features (dict)
    """
    subject = subject or ""
    body_text = body_text or ""
    from_addr = from_addr or ""
    reply_to = reply_to or ""

    text = f"{subject}\n{body_text}".lower()

    reasons = []
    features = {}

    score = 0

    # 1) URLs
    urls = extract_urls(body_text)
    features["urls"] = urls
    if urls:
        score += 15
        reasons.append("This email contains one or more links, which is common in phishing.")

        suspicious_url_count = 0
        shorteners = 0
        ip_links = 0

        for u in urls:
            dom = domain_of(u) or ""
            if dom in SHORTENER_DOMAINS:
                shorteners += 1
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", dom):
                ip_links += 1
            # lookalike-ish: many hyphens or long host
            if dom.count("-") >= 3 or len(dom) >= 28:
                suspicious_url_count += 1

        features["url_shorteners"] = shorteners
        features["url_ip_links"] = ip_links
        features["url_suspicious_host_count"] = suspicious_url_count

        if shorteners > 0:
            score += 15
            reasons.append("A link shortener is used, which can hide the real destination.")
        if ip_links > 0:
            score += 20
            reasons.append("A link points directly to an IP address, which is suspicious.")
        if suspicious_url_count > 0:
            score += 10
            reasons.append("Some link domains look unusual (very long or many hyphens).")

    # 2) Urgency / fear / account pressure
    urgency_hits = [k for k in URGENT_KEYWORDS if k in text]
    features["urgency_hits"] = urgency_hits
    if urgency_hits:
        score += 20
        reasons.append("The message uses urgency/pressure language (a common scam tactic).")

    # 3) Credential harvesting wording
    cred_hits = [k for k in CREDENTIAL_KEYWORDS if k in text]
    features["credential_hits"] = cred_hits
    if cred_hits:
        score += 20
        reasons.append("The message asks you to log in/verify credentials (possible credential harvesting).")

    # 4) Authority cues
    auth_hits = [k for k in AUTHORITY_KEYWORDS if k in text]
    features["authority_hits"] = auth_hits
    if auth_hits:
        score += 10
        reasons.append("The message uses authority cues (CEO/IT/Security), a common manipulation method.")

    # 5) Sender mismatch: From vs Reply-To
    if from_addr and reply_to and (from_addr.lower() != reply_to.lower()):
        score += 15
        features["from_reply_to_mismatch"] = True
        reasons.append("Reply-To differs from From, which can indicate impersonation.")
    else:
        features["from_reply_to_mismatch"] = False

    # Clamp score
    score = max(0, min(100, score))

    # Verdict
    if score >= 70:
        verdict = "phishing"
    elif score >= 40:
        verdict = "suspicious"
    else:
        verdict = "safe"

    # Taxonomy labeling (simple rules)
    if cred_hits:
        attack_type = "Credential Harvesting"
    elif "invoice" in text or "payment" in text or "wire" in text or "transfer" in text:
        attack_type = "Invoice/Payment Fraud"
    elif features.get("from_reply_to_mismatch"):
        attack_type = "Impersonation/Spoofing"
    else:
        attack_type = "General Social Engineering"

    if urgency_hits:
        manipulation_strategy = "Urgency/Pressure"
    elif auth_hits:
        manipulation_strategy = "Authority"
    else:
        manipulation_strategy = "Unknown/Other"

    return {
        "risk_score": score,
        "verdict": verdict,
        "attack_type": attack_type,
        "manipulation_strategy": manipulation_strategy,
        "reasons": reasons[:8],
        "features": features,
    }


def to_json_text(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)