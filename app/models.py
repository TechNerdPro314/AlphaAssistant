# app/models.py
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telegram_id = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    business_profile = db.relationship(
        "BusinessProfile", backref="user", uselist=False, lazy=True
    )
    chat_sessions = db.relationship("ChatSession", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class BusinessProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    industry = db.Column(db.String(120))
    company_size = db.Column(db.String(50))
    goals = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True
    )

    def __repr__(self):
        return f"<BusinessProfile for User {self.user_id}>"


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    messages = db.relationship(
        "Message", backref="chat_session", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSession {self.id}>"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    session_id = db.Column(db.Integer, db.ForeignKey("chat_session.id"), nullable=False)

    def __repr__(self):
        return f"<Message {self.id} in Session {self.session_id}>"
