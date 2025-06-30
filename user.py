from flask_login import UserMixin
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from .models import UserProgress

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default='A1')

    # Relations avec les autres modèles
    progress = db.relationship('UserProgress', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")
    completed_dialogues = db.relationship('CompletedDialogue', backref='user', lazy=True, cascade="all, delete-orphan")
    badges = db.relationship('UserBadge', backref='user', lazy=True, cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.progress:
            self.progress = UserProgress(points=0, level=1)
        if not self.username and self.email:
            self.username = self.email.split('@')[0]

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username or self.email}>'