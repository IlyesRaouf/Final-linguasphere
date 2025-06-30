from .extensions import db
from datetime import datetime

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def add_points(self, points):
        """Ajoute des points et met à jour le niveau si nécessaire"""
        self.points += points
        self.last_activity = datetime.utcnow()
        
        # Logique de progression de niveau (à ajuster selon vos besoins)
        level_thresholds = {
            1: 0,     # Niveau 1: 0-99 points
            2: 100,   # Niveau 2: 100-249 points
            3: 250,   # Niveau 3: 250-499 points
            4: 500,   # Niveau 4: 500-999 points
            5: 1000,  # Niveau 5: 1000+ points
        }
        
        # Déterminer le niveau en fonction des points
        for level, threshold in sorted(level_thresholds.items(), key=lambda x: x[1], reverse=True):
            if self.points >= threshold:
                if self.level < level:
                    # L'utilisateur a gagné un niveau
                    self.level = level
                    # Ici, on pourrait ajouter un badge pour le nouveau niveau
                break

class CompletedDialogue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dialogue_id = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contrainte d'unicité pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('user_id', 'dialogue_id', name='unique_user_dialogue'),)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(100))  # Chemin vers l'icône du badge
    
    # Relation avec UserBadge
    users = db.relationship('UserBadge', backref='badge_info', lazy=True)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contrainte d'unicité pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'dialogue_completed', 'level_up', 'badge_earned', etc.
    description = db.Column(db.String(200))
    points_earned = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def log(cls, user_id, activity_type, description, points_earned=0):
        """Méthode utilitaire pour enregistrer une activité"""
        activity = cls(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            points_earned=points_earned
        )
        db.session.add(activity)
        return activity

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)