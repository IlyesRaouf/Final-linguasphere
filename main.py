# -*- coding: utf-8 -*-

from flask import Flask
from .extensions import db, login_manager
from .config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialiser la base de données
    db.init_app(app)

    # Initialiser Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Définir la fonction pour charger un utilisateur
    from .user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from .routes.auth_routes import auth_bp
        from .routes.main_routes import main_bp

        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(main_bp)

        db.create_all()

    return app