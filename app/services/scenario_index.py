import json
from pathlib import Path
from typing import List, Dict, Any


def list_scenarios() -> List[Dict[str, Any]]:
    base_dir = Path(__file__).resolve().parent.parent  # /app
    scenarios_dir = base_dir / "scenarios"
    out: List[Dict[str, Any]] = []

    for p in sorted(scenarios_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        out.append({
            "id": data.get("id", p.stem),
            "difficulty": data.get("difficulty", "easy"),
            "channel": data.get("channel", "email"),
            "manipulation_type": data.get("manipulation_type", "UNKNOWN"),
        })
    return out