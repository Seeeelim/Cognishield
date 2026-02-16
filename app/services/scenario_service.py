import json
from pathlib import Path
from typing import Any, Dict


def load_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Load a scenario JSON by its id (filename without .json) from app/scenarios/.
    Example: scenario_id='email_001' -> app/scenarios/email_001.json
    """
    base_dir = Path(__file__).resolve().parent.parent  # points to /app
    scenario_path = base_dir / "scenarios" / f"{scenario_id}.json"

    if not scenario_path.exists() or not scenario_path.is_file():
        raise FileNotFoundError(f"Scenario not found: {scenario_id}")

    with scenario_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic sanity checks (prevents template crashes)
    required_keys = ["id", "channel", "story", "artifact", "choices", "correct_choice", "feedback"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"Scenario is missing required key: {k}")

    return data