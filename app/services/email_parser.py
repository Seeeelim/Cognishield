from email import policy
from email.parser import BytesParser
from email.message import Message
from typing import Optional, Dict


def _get_header(msg: Message, name: str) -> Optional[str]:
    value = msg.get(name)
    return str(value) if value is not None else None


def _get_text_body(msg: Message) -> Optional[str]:
    """
    Best-effort extraction of text content from an email message.
    Prefer text/plain; fall back to other text/* parts.
    """
    if msg.is_multipart():
        # Prefer text/plain
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    return payload.decode(errors="replace") if payload else None

        # Fallback: any text/*
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type().startswith("text/"):
                try:
                    return part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    return payload.decode(errors="replace") if payload else None

        return None

    # Not multipart
    try:
        return msg.get_content()
    except Exception:
        payload = msg.get_payload(decode=True)
        return payload.decode(errors="replace") if payload else None


def parse_eml_bytes(eml_bytes: bytes) -> Dict[str, Optional[str]]:
    """
    Parse .eml bytes and extract headers + text body.
    Returns a dict compatible with EmailRecord fields.
    """
    msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)

    headers_lines = []
    for k, v in msg.items():
        headers_lines.append(f"{k}: {v}")
    headers_text = "\n".join(headers_lines)

    body_text = _get_text_body(msg) or ""

    return {
        "subject": _get_header(msg, "Subject"),
        "from_addr": _get_header(msg, "From"),
        "reply_to": _get_header(msg, "Reply-To"),
        "return_path": _get_header(msg, "Return-Path"),
        "headers_text": headers_text[:20000],
        "body_text": body_text[:200000],
    }