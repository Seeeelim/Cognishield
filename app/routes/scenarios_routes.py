import json
from pathlib import Path
from typing import List, Dict, Any

from flask import Blueprint, render_template, abort, jsonify
from app.services.scenario_service import load_scenario

scenarios_bp = Blueprint("scenarios", __name__)


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


@scenarios_bp.get("/play/<scenario_id>")
def play_scenario(scenario_id: str):
    try:
        scenario = load_scenario(scenario_id)
    except FileNotFoundError:
        abort(404)
    except ValueError:
        abort(500)

    return render_template("play.html", scenario=scenario)


@scenarios_bp.get("/progress")
def progress():
    return render_template("progress.html")


@scenarios_bp.get("/api/scenarios")
def api_scenarios():
    return jsonify(list_scenarios())
