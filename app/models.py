from datetime import datetime
from app import db

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailRecord(db.Model):
    """
    Represents a single email message that the platform ingests (from .eml upload, paste, or dataset import).
    """
    __tablename__ = "email_records"

    id = db.Column(db.Integer, primary_key=True)

    # Minimal parsed fields (safe and useful)
    subject = db.Column(db.String(500), nullable=True)
    from_addr = db.Column(db.String(500), nullable=True)
    reply_to = db.Column(db.String(500), nullable=True)
    return_path = db.Column(db.String(500), nullable=True)

    # Store a text version for MVP. (We can store raw_source optionally later.)
    body_text = db.Column(db.Text, nullable=True)

    # Optional: store a truncated header text (not required)
    headers_text = db.Column(db.Text, nullable=True)

    ingested_via = db.Column(db.String(50), default="upload")  # upload / paste / dataset
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DetectionResult(db.Model):
    """
    Stores detection output: score, taxonomy labels, and explanation reasons.
    """
    __tablename__ = "detection_results"

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("email_records.id"), nullable=False, index=True)

    risk_score = db.Column(db.Integer, nullable=False)  # 0-100
    verdict = db.Column(db.String(50), nullable=False)  # safe/suspicious/phishing/impersonation/fraud

    attack_type = db.Column(db.String(100), nullable=False)  # Credential Harvesting, Brand Impersonation, etc.
    manipulation_strategy = db.Column(db.String(100), nullable=False)  # Urgency, Authority, Fear, Reward

    # Store explanations and features as JSON strings for MVP (simple).
    reasons_json = db.Column(db.Text, nullable=True)
    features_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    email = db.relationship("EmailRecord", backref=db.backref("detection_results", lazy=True))


class BehaviorEvent(db.Model):
    """
    Records what an employee did in response to an email inside our platform (MVP).
    """
    __tablename__ = "behavior_events"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True)
    email_id = db.Column(db.Integer, db.ForeignKey("email_records.id"), nullable=False, index=True)

    event_type = db.Column(db.String(50), nullable=False)
    # examples: viewed, clicked_link, reported, marked_safe, unsure

    event_time = db.Column(db.DateTime, default=datetime.utcnow)
    metadata_json = db.Column(db.Text, nullable=True)  # e.g. which URL was clicked

    employee = db.relationship("Employee", backref=db.backref("events", lazy=True))
    email = db.relationship("EmailRecord", backref=db.backref("events", lazy=True))