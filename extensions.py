from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour entrer la page."
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(user_id):
    from .user import User
    return User.query.get(int(user_id))