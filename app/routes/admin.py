from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Employee, EmailRecord
from app.services.email_parser import parse_eml_bytes
from app.models import Employee, EmailRecord, DetectionResult, BehaviorEvent
from app.services.detection_engine import score_email, to_json_text
import json
from app.services.detection_engine import extract_urls

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def _log_event(employee_id: int, email_id: int, event_type: str, metadata: dict | None = None):
    evt = BehaviorEvent(
        employee_id=employee_id,
        email_id=email_id,
        event_type=event_type,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False)
    )
    db.session.add(evt)
    db.session.commit()
    return evt

@admin_bp.route("/")
def admin_home():
    return render_template("admin/admin_home.html")

# -------------------------
# Employees
# -------------------------
@admin_bp.route("/employees", methods=["GET"])
def employees_list():
    employees = Employee.query.order_by(Employee.created_at.desc()).all()
    return render_template("admin/employee_list.html", employees=employees)


@admin_bp.route("/employees/new", methods=["GET", "POST"])
def employees_new():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip() or None
        department = request.form.get("department", "").strip() or None

        if not email:
            flash("Email is required.", "danger")
            return render_template("admin/employee_new.html")

        existing = Employee.query.filter_by(email=email).first()
        if existing:
            flash("Employee with this email already exists.", "danger")
            return render_template("admin/employee_new.html")

        emp = Employee(email=email, full_name=full_name, department=department)
        db.session.add(emp)
        db.session.commit()

        flash("Employee created ✅", "success")
        return redirect(url_for("admin.employees_list"))

    return render_template("admin/employee_new.html")

# -------------------------
# Email ingestion
# -------------------------
@admin_bp.route("/emails", methods=["GET"])
def emails_list():
    emails = EmailRecord.query.order_by(EmailRecord.created_at.desc()).all()
    return render_template("admin/emails_list.html", emails=emails)

@admin_bp.route("/emails/<int:email_id>")
def email_view(email_id):
    email = EmailRecord.query.get_or_404(email_id)

    employees = Employee.query.order_by(Employee.created_at.desc()).all()

    latest_detection = None
    if email.detection_results:
        latest_detection = sorted(email.detection_results, key=lambda d: d.created_at)[-1]

    urls = extract_urls(email.body_text or "")

    # Get recent events for this email (last 50)
    events = BehaviorEvent.query.filter_by(email_id=email.id).order_by(BehaviorEvent.event_time.desc()).limit(50).all()

    return render_template(
        "admin/email_view.html",
        email=email,
        detection=latest_detection,
        employees=employees,
        urls=urls,
        events=events
    )

@admin_bp.route("/emails/<int:email_id>/action", methods=["POST"])
def email_action(email_id):
    email = EmailRecord.query.get_or_404(email_id)

    employee_id = request.form.get("employee_id", "").strip()
    event_type = request.form.get("event_type", "").strip()

    if not employee_id or not event_type:
        flash("Please select an employee and an action.", "danger")
        return redirect(url_for("admin.email_view", email_id=email.id))

    employee_id_int = int(employee_id)

    if event_type not in {"reported", "marked_safe", "unsure"}:
        flash("Invalid action.", "danger")
        return redirect(url_for("admin.email_view", email_id=email.id))

    _log_event(employee_id_int, email.id, event_type)
    flash(f"Event logged: {event_type} ✅", "success")
    return redirect(url_for("admin.email_view", email_id=email.id))

@admin_bp.route("/emails/<int:email_id>/click", methods=["POST"])
def email_click(email_id):
    email = EmailRecord.query.get_or_404(email_id)

    employee_id = request.form.get("employee_id", "").strip()
    url_clicked = request.form.get("url", "").strip()

    if not employee_id or not url_clicked:
        flash("Please select an employee and a link.", "danger")
        return redirect(url_for("admin.email_view", email_id=email.id))

    employee_id_int = int(employee_id)

    _log_event(employee_id_int, email.id, "clicked_link", {"url": url_clicked})
    flash("Event logged: clicked_link ✅", "success")

    # We do NOT actually open the URL (safe). We just simulate the click.
    return redirect(url_for("admin.email_view", email_id=email.id))

@admin_bp.route("/emails/<int:email_id>/detect", methods=["POST"])
def email_detect(email_id):
    email = EmailRecord.query.get_or_404(email_id)

    result = score_email(
        subject=email.subject,
        from_addr=email.from_addr,
        reply_to=email.reply_to,
        body_text=email.body_text,
    )

    det = DetectionResult(
        email_id=email.id,
        risk_score=result["risk_score"],
        verdict=result["verdict"],
        attack_type=result["attack_type"],
        manipulation_strategy=result["manipulation_strategy"],
        reasons_json=to_json_text(result["reasons"]),
        features_json=to_json_text(result["features"]),
    )
    db.session.add(det)
    db.session.commit()

    flash("Detection executed ✅", "success")
    return redirect(url_for("admin.email_view", email_id=email.id))

@admin_bp.route("/emails/new", methods=["GET", "POST"])
def emails_new():
    if request.method == "POST":
        ingested_via = request.form.get("ingested_via", "upload")

        # Option A: upload .eml file
        eml_file = request.files.get("eml_file")

        # Option B: paste content
        pasted_subject = request.form.get("subject", "").strip() or None
        pasted_from = request.form.get("from_addr", "").strip() or None
        pasted_reply_to = request.form.get("reply_to", "").strip() or None
        pasted_return_path = request.form.get("return_path", "").strip() or None
        pasted_headers = request.form.get("headers_text", "").strip() or None
        pasted_body = request.form.get("body_text", "").strip() or None

        if eml_file and eml_file.filename:
            # Read bytes and parse
            data = eml_file.read()
            parsed = parse_eml_bytes(data)

            rec = EmailRecord(
                subject=parsed.get("subject"),
                from_addr=parsed.get("from_addr"),
                reply_to=parsed.get("reply_to"),
                return_path=parsed.get("return_path"),
                headers_text=parsed.get("headers_text"),
                body_text=parsed.get("body_text"),
                ingested_via="upload",
            )
            db.session.add(rec)
            db.session.commit()
            flash("Email ingested from .eml ✅", "success")
            return redirect(url_for("admin.emails_list"))

        # If no file, require pasted body at least
        if not pasted_body and not pasted_headers and not pasted_subject:
            flash("Please upload a .eml file OR paste email content.", "danger")
            return render_template("admin/email_new.html")

        rec = EmailRecord(
            subject=pasted_subject,
            from_addr=pasted_from,
            reply_to=pasted_reply_to,
            return_path=pasted_return_path,
            headers_text=pasted_headers,
            body_text=pasted_body,
            ingested_via="paste",
        )
        db.session.add(rec)
        db.session.commit()
        flash("Email ingested from pasted content ✅", "success")
        return redirect(url_for("admin.emails_list"))

    return render_template("admin/email_new.html")