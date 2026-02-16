from flask import Blueprint, render_template, abort
from app.services.scenario_service import load_scenario

scenarios_bp = Blueprint("scenarios", __name__)


@scenarios_bp.get("/play/<scenario_id>")
def play_scenario(scenario_id: str):
    try:
        scenario = load_scenario(scenario_id)
    except FileNotFoundError:
        abort(404)
    except ValueError:
        abort(500)

    return render_template("play.html", scenario=scenario)