from datetime import datetime
from app import db

class Learner(db.Model):
    __tablename__ = "learners"
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    experience_level = db.Column(db.String(50), default="beginner")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Scenario(db.Model):
    __tablename__ = "scenarios"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(50), default="email")
    subject = db.Column(db.String(255), nullable=True)
    body_text = db.Column(db.Text, nullable=False)
    attack_type = db.Column(db.String(100), nullable=False)
    manipulation_strategy = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    explanation_plain = db.Column(db.Text, nullable=False)
    red_flags = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attempt(db.Model):
    __tablename__ = "attempts"
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey("learners.id"), nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey("scenarios.id"), nullable=False)
    choice = db.Column(db.String(50), nullable=False)  # safe/unsafe/report/unsure
    is_correct = db.Column(db.Boolean, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=True)
    hints_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    learner = db.relationship("Learner", backref="attempts")
    scenario = db.relationship("Scenario", backref="attempts")