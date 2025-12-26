from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Learner, Scenario

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
def admin_home():
    return render_template("admin/admin_home.html")

@admin_bp.route("/learners")
def learners_list():
    learners = Learner.query.order_by(Learner.created_at.desc()).all()
    return render_template("admin/learners_list.html", learners=learners)

@admin_bp.route("/learners/new", methods=["GET", "POST"])
def learners_new():
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip() or None
        email = request.form.get("email", "").strip().lower() or None
        experience_level = request.form.get("experience_level", "beginner").strip() or "beginner"

        learner = Learner(display_name=display_name, email=email, experience_level=experience_level)
        db.session.add(learner)
        db.session.commit()

        flash("Learner created ✅", "success")
        return redirect(url_for("admin.learners_list"))

    return render_template("admin/learner_new.html")

@admin_bp.route("/scenarios")
def scenarios_list():
    scenarios = Scenario.query.order_by(Scenario.created_at.desc()).all()
    return render_template("admin/scenarios_list.html", scenarios=scenarios)

@admin_bp.route("/scenarios/new", methods=["GET", "POST"])
def scenarios_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip() or None
        body_text = request.form.get("body_text", "").strip()
        attack_type = request.form.get("attack_type", "").strip()
        manipulation_strategy = request.form.get("manipulation_strategy", "").strip()
        difficulty = int(request.form.get("difficulty", "1"))
        explanation_plain = request.form.get("explanation_plain", "").strip()
        red_flags = request.form.get("red_flags", "").strip() or None

        if not title or not body_text or not attack_type or not manipulation_strategy or not explanation_plain:
            flash("Missing required fields.", "danger")
            return render_template("admin/scenario_new.html")

        scenario = Scenario(
            title=title, subject=subject, body_text=body_text,
            attack_type=attack_type, manipulation_strategy=manipulation_strategy,
            difficulty=difficulty, explanation_plain=explanation_plain, red_flags=red_flags
        )
        db.session.add(scenario)
        db.session.commit()

        flash("Scenario created ✅", "success")
        return redirect(url_for("admin.scenarios_list"))

    return render_template("admin/scenario_new.html")