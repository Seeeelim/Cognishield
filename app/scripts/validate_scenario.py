import json
import sys
from pathlib import Path

ALLOWED_MANIPULATION_TYPES = {
    "URGENT_ACTION",
    "AUTHORITY_IMPERSONATION",
    "EMOTIONAL_LEVERAGE",
    "REWARD_LURE",
    "TECH_SUPPORT_DECEPTION",
    "TRUSTED_CHANNEL_ABUSE",
}

ALLOWED_TARGET_ASSETS = {
    "credentials",
    "money_transfer",
    "pii",
    "device_access",
    "account_takeover",
    "install_malware",
}

ALLOWED_PERSUASION_TACTICS = {
    "urgency",
    "fear",
    "authority",
    "scarcity",
    "curiosity",
    "reciprocity",
    "commitment",
    "social_proof",
    "shame_guilt",
    "convenience",
}

REQUIRED_TOP_KEYS = [
    "id",
    "channel",
    "difficulty",
    "story",
    "artifact",
    "choices",
    "correct_choice",
    "feedback",
    "manipulation_type",
    "persuasion_tactics",
    "target_asset",
    "mitre_attack",
]

ALLOWED_CHANNELS = {"email", "sms", "qr"}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}


def fail(msg: str) -> None:
    print(f"[ERROR] {msg}")
    sys.exit(1)


def validate_file(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"{path}: invalid JSON ({e})")

    for k in REQUIRED_TOP_KEYS:
        if k not in data:
            fail(f"{path}: missing key '{k}'")

    if not isinstance(data["id"], str) or not data["id"]:
        fail(f"{path}: 'id' must be a non-empty string")

    if data["channel"] not in ALLOWED_CHANNELS:
        fail(f"{path}: 'channel' must be one of {sorted(ALLOWED_CHANNELS)}")

    if data["difficulty"] not in ALLOWED_DIFFICULTY:
        fail(f"{path}: 'difficulty' must be one of {sorted(ALLOWED_DIFFICULTY)}")

    if not isinstance(data["story"], dict) or "title" not in data["story"] or "context" not in data["story"]:
        fail(f"{path}: 'story' must be an object with 'title' and 'context'")

    if not isinstance(data["artifact"], dict) or "from" not in data["artifact"] or "subject" not in data["artifact"] or "body" not in data["artifact"]:
        fail(f"{path}: 'artifact' must be an object with 'from', 'subject', 'body'")

    if not isinstance(data["choices"], list) or len(data["choices"]) < 2:
        fail(f"{path}: 'choices' must be a list with at least 2 items")

    # manipulation_type
    if data["manipulation_type"] not in ALLOWED_MANIPULATION_TYPES:
        fail(f"{path}: 'manipulation_type' must be one of {sorted(ALLOWED_MANIPULATION_TYPES)}")

    # persuasion_tactics
    if not isinstance(data["persuasion_tactics"], list) or not data["persuasion_tactics"]:
        fail(f"{path}: 'persuasion_tactics' must be a non-empty list")
    for t in data["persuasion_tactics"]:
        if not isinstance(t, str) or t not in ALLOWED_PERSUASION_TACTICS:
            fail(f"{path}: invalid persuasion tactic '{t}' (allowed: {sorted(ALLOWED_PERSUASION_TACTICS)})")

    # target_asset
    if data["target_asset"] not in ALLOWED_TARGET_ASSETS:
        fail(f"{path}: 'target_asset' must be one of {sorted(ALLOWED_TARGET_ASSETS)}")

    # mitre_attack
    if not isinstance(data["mitre_attack"], dict):
        fail(f"{path}: 'mitre_attack' must be an object")
    if "tactics" not in data["mitre_attack"] or "techniques" not in data["mitre_attack"]:
        fail(f"{path}: 'mitre_attack' must include 'tactics' and 'techniques'")
    if not isinstance(data["mitre_attack"]["tactics"], list) or not all(isinstance(x, str) and x for x in data["mitre_attack"]["tactics"]):
        fail(f"{path}: 'mitre_attack.tactics' must be a list of non-empty strings")
    if not isinstance(data["mitre_attack"]["techniques"], list) or not all(isinstance(x, str) and x for x in data["mitre_attack"]["techniques"]):
        fail(f"{path}: 'mitre_attack.techniques' must be a list of non-empty strings")

    choice_ids = []
    for c in data["choices"]:
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            fail(f"{path}: each choice must be an object with 'id' and 'text'")
        if not isinstance(c["id"], str) or not c["id"]:
            fail(f"{path}: choice 'id' must be a non-empty string")
        if c["id"] in choice_ids:
            fail(f"{path}: duplicate choice id '{c['id']}'")
        choice_ids.append(c["id"])

    if data["correct_choice"] not in choice_ids:
        fail(f"{path}: 'correct_choice' must match one of choice ids {choice_ids}")

    if not isinstance(data["feedback"], dict):
        fail(f"{path}: 'feedback' must be an object mapping choice id -> text")

    for cid in choice_ids:
        if cid not in data["feedback"]:
            fail(f"{path}: feedback missing for choice '{cid}'")
        if not isinstance(data["feedback"][cid], str) or not data["feedback"][cid]:
            fail(f"{path}: feedback for '{cid}' must be a non-empty string")

    # Optional tags checks
    for tag_field in ("bias_tags", "attack_tags"):
        if tag_field in data:
            if not isinstance(data[tag_field], list) or any(not isinstance(x, str) or not x for x in data[tag_field]):
                fail(f"{path}: '{tag_field}' must be a list of non-empty strings")

    # Consistency check: file name should match scenario id
    if path.stem != data["id"]:
        fail(f"{path}: filename '{path.stem}' must match scenario id '{data['id']}'")

    print(f"[OK] {path.name}")


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    scenarios_dir = base / "app" / "scenarios"

    if not scenarios_dir.exists():
        fail(f"scenarios directory not found: {scenarios_dir}")

    files = sorted(scenarios_dir.glob("*.json"))
    if not files:
        fail(f"no scenario JSON files found in {scenarios_dir}")

    for f in files:
        validate_file(f)

    print(f"\nAll scenarios validated: {len(files)} file(s).")


if __name__ == "__main__":
    main()