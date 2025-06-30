from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..user import User

auth_bp = Blueprint("auth", __name__, template_folder="templates")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([username, email, password]):
            flash("Tous les champs sont obligatoires", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Nom d'utilisateur ou email déjà utilisé.", "error")
            return redirect(url_for("auth.register"))

        try:
            new_user = User(email=email, username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            session['user_id'] = new_user.id
            flash("Inscription réussie !", "success")
            return redirect(url_for("main_bp.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue : {e}", "error")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return redirect(url_for("auth.login"))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            flash("Connexion réussie !", "success")
            return redirect(url_for("main_bp.dashboard"))
        else:
            flash("Email ou mot de passe incorrect.", "error")
            return redirect(url_for("auth.login"))
    
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash("Déconnexion réussie.", "success")
    return redirect(url_for("main_bp.home"))